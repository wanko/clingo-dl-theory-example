# TODO:
# - only having a way to lookup symbols in linear time is not sufficient

import ctypes
import clingo

from ctypes import c_bool, c_void_p, c_int, c_double, c_uint, c_uint64, c_size_t, Union, Structure, POINTER, byref

class _c_value(Union):
    _fields_ = [ ("integer", c_int)
               , ("double", c_double)
               , ("symbol", c_uint64)
               ]

class _c_variant(Structure):
    _fields_ = [ ("type", c_int)
               , ("value", _c_value)
               ]

class Theory:
    def __init__(self, prefix, lib):
        # load library
        self.__theory = ctypes.cdll.LoadLibrary("libclingo-dl.so")

        # bool create_propagator(propagator_t **propagator);
        self.__create_propagator = self.__fun(prefix, "create_propagator", c_bool, [POINTER(c_void_p)])

        # bool destroy_propagator(propagator_t *propagator);
        self.__destroy_propagator = self.__fun(prefix, "destroy_propagator", c_bool, [c_void_p])

        # bool register_propagator(propagator_t *propagator, clingo_control_t* control);
        self.__register_propagator = self.__fun(prefix, "register_propagator", c_bool, [c_void_p, c_void_p])

        # bool register_options(propagator_t *propagator, clingo_options_t* options);
        self.__register_options = self.__fun(prefix, "register_options", c_bool, [c_void_p, c_void_p])

        # bool validate_options(propagator_t *propagator);
        self.__validate_options = self.__fun(prefix, "validate_options", c_bool, [c_void_p])

        # bool on_model(propagator_t *propagator, clingo_model_t* model);
        self.__on_model = self.__fun(prefix, "on_model", c_bool, [c_void_p, c_void_p])

        # void assignment_begin(propagator_t *propagator, uint32_t thread_id, size_t *index);
        self.__assignment_begin = self.__fun(prefix, "assignment_begin", c_bool, [c_void_p, c_uint, POINTER(c_size_t)])

        # bool assignment_next(propagator_t *propagator, uint32_t thread_id, size_t *index, clingo_symbol_t *name, value_t* value, bool *result);
        self.__assignment_next = self.__fun(prefix, "assignment_next", c_bool, [c_void_p, c_uint, POINTER(c_size_t), POINTER(c_uint64), POINTER(_c_variant), POINTER(c_bool)])

        # bool on_statistics(propagator_t *propagator, clingo_statistics_t* step, clingo_statistics_t* accu);
        self.__on_statistics = self.__fun(prefix, "on_statistics", c_bool, [c_void_p, c_void_p, c_void_p])

        # create propagator
        self.__c_propagator = c_void_p()
        self.__create_propagator(byref(self.__c_propagator));

    def __del__(self):
        self.__destroy_propagator(self.__c_propagator)

    def register_propagator(self, control):
        control_ptr = c_void_p(control._to_c)
        self.__register_propagator(self.__c_propagator, control_ptr)

    def register_options(self, options):
        options_ptr = c_void_p(options._to_c)
        self.__register_options(self.__c_propagator, options_ptr)

    def validate_options(self):
        self.__validate_options(self.__c_propagator)

    def on_model(self, model):
        model_ptr = c_void_p(model._to_c)
        self.__on_model(self.__c_propagator, model_ptr)

    def on_statistics(self, step, accu):
        step_ptr = c_void_p(step._to_c)
        accu_ptr = c_void_p(accu._to_c)
        self.__on_statistics(self.__c_propagator, step_ptr, accu_ptr)

    def assignment(self, thread_id):
        c_id = c_uint(thread_id)
        c_index = c_size_t()
        c_value = _c_variant()
        c_name = c_uint64()
        c_result = c_bool()
        self.__assignment_begin(self.__c_propagator, c_id, byref(c_index))
        while True:
            self.__assignment_next(self.__c_propagator, c_id, byref(c_index), byref(c_name), byref(c_value), byref(c_result))
            if c_result.value:
                name = clingo._Symbol(c_name.value)
                if c_value.type == 0:
                    yield (name, c_value.value.integer)
                elif c_value.type == 1:
                    yield (name, c_value.value.double)
                elif c_value.type == 2:
                    yield (name, clingo._Symbol(c_value.value.symbol))
            else:
                break

    def __fun(self, prefix, name, res, args):
        ret = self.__theory["{}_{}".format(prefix, name)]
        ret.restype  = res
        ret.argtypes = args
        ret.errcheck = self.__handle_error
        return ret

    def __handle_error(self, success, func, arguments):
        if not success:
            code = clingo._error_code()
            msg  = clingo._error_message()
            if msg is None:
                msg = "no message"
            if code == 1 or code == 2 or code == 4:
                raise RuntimeError(msg)
            if code == 3:
                raise MemoryError(msg)
            raise RuntimeError("unknow error")

