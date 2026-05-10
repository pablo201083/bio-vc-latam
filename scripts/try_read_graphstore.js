var gephiPath = arguments.length > 0 ? arguments[0] : "C:/Users/Pablo A/Desktop/Ecosistema Startups Materiales Universidades Fondos Startups 426112025.gephi";
var entryName = arguments.length > 1 ? arguments[1] : "Workspace_1_graphstore_bytes";

var ZipFile = Java.type("java.util.zip.ZipFile");
var ByteArrayOutputStream = Java.type("java.io.ByteArrayOutputStream");
var DataInputOutput = Java.type("org.gephi.graph.impl.utils.DataInputOutput");
var GraphModelSerialization = Java.type("org.gephi.graph.api.GraphModel$Serialization");
var SerializationImpl = Java.type("org.gephi.graph.impl.Serialization");
var BytePrimitive = Java.type("java.lang.Byte").TYPE;
var Array = Java.type("java.lang.reflect.Array");

function readZipEntry(path, name) {
  var zip = new ZipFile(path);
  try {
    var entry = zip.getEntry(name);
    if (entry == null) {
      throw new Error("Missing zip entry: " + name);
    }
    var input = zip.getInputStream(entry);
    try {
      var out = new ByteArrayOutputStream();
      var buffer = Array.newInstance(BytePrimitive, 8192);
      var read;
      while ((read = input.read(buffer)) !== -1) {
        out.write(buffer, 0, read);
      }
      return out.toByteArray();
    } finally {
      input.close();
    }
  } finally {
    zip.close();
  }
}

function tryRead(label, fn) {
  try {
    var model = fn();
    var graph = model.getGraph();
    print("SUCCESS " + label);
    print("nodes=" + graph.getNodeCount());
    print("edges=" + graph.getEdgeCount());
  } catch (e) {
    print("FAIL " + label + " -> " + e);
    if (e.javaException) {
      e.javaException.printStackTrace();
    }
  }
}

var bytes = readZipEntry(gephiPath, entryName);
print("bytes=" + bytes.length);

tryRead("GraphModel.Serialization.read", function () {
  return GraphModelSerialization.read(new DataInputOutput(bytes));
});

tryRead("GraphModel.Serialization.readWithoutVersionHeader.0.9", function () {
  return GraphModelSerialization.readWithoutVersionHeader(new DataInputOutput(bytes), 0.9);
});

tryRead("GraphModel.Serialization.readWithoutVersionHeader.1.0", function () {
  return GraphModelSerialization.readWithoutVersionHeader(new DataInputOutput(bytes), 1.0);
});

tryRead("Serialization.deserializeGraphModel", function () {
  var s = new SerializationImpl();
  return s.deserializeGraphModel(new DataInputOutput(bytes));
});

tryRead("Serialization.deserializeGraphModelWithoutVersionPrefix.0.9", function () {
  var s = new SerializationImpl();
  return s.deserializeGraphModelWithoutVersionPrefix(new DataInputOutput(bytes), 0.9);
});
