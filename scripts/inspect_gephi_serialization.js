var target = arguments.length > 0 ? arguments[0] : "org.gephi.graph.impl.Serialization";
var Cls = Java.type(target);
print(String(Cls.class));
var methods = Cls.class.getDeclaredMethods();
for each (var m in methods) {
  print(String(m));
}
