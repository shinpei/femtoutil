/*
 * Dependable FFI
 *  CLib: library wrapper generator using libffi
 *  Process : process wrapper generator.
 */

//include nativelink;
include "lib:gluelink";

@Native class Clib;
@Native Clib Clib.new(String libname, Clib _);
@Native class Structure;
//@Native Structure Structure.new(Array<Tuple<String, Int>> values, Structure _);
@Native Structure Structure.new(Array<Array<dynamic>> values, Structure _);

@Native class Process;
@Native Process Process.new(String path, Process _);

@Native class Webservice;
@Native Webservice Webservice.new(String url, Webservice _);

@Native class Glue;
@Native var Glue.getFunc(String symbol, Class _, Func _);
//@Native Method Glue.getFunc(String symbol, Class _, Func _);

@Native Glue Clib.genGlue(Glue _);
@Native Glue Process.genGlue(Glue _);
//@Native Glue Webservice.genGlue(Glue _);

@Native void Clib.defineClass(String classname, Structure strc, NameSpace _);

