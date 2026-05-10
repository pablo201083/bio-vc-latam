var gephiPath = arguments.length > 0 ? arguments[0] : "C:/Users/Pablo A/Desktop/Ecosistema Startups Materiales Universidades Fondos Startups 426112025.gephi";
var outputDir = arguments.length > 1 ? arguments[1] : "C:/Users/Pablo A/Documents/Codex/2026-04-18-summarize-what-s-happening-on-slack/staging/full_gephi_graph";

var ZipFile = Java.type("java.util.zip.ZipFile");
var ByteArrayOutputStream = Java.type("java.io.ByteArrayOutputStream");
var BytePrimitive = Java.type("java.lang.Byte").TYPE;
var Array = Java.type("java.lang.reflect.Array");
var DataInputOutput = Java.type("org.gephi.graph.impl.utils.DataInputOutput");
var GraphModelSerialization = Java.type("org.gephi.graph.api.GraphModel$Serialization");
var File = Java.type("java.io.File");
var PrintWriter = Java.type("java.io.PrintWriter");
var LinkedHashMap = Java.type("java.util.LinkedHashMap");

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

function toJsArray(javaIterable) {
  return Java.from(javaIterable.toArray());
}

function csvEscape(value) {
  if (value === null || value === undefined) {
    return "";
  }
  var text = String(value);
  if (text.indexOf('"') >= 0) {
    text = text.replace(/"/g, '""');
  }
  if (/[",\r\n]/.test(text)) {
    return '"' + text + '"';
  }
  return text;
}

function writeCsv(path, headers, rows) {
  var writer = new PrintWriter(path, "UTF-8");
  try {
    writer.println(headers.map(csvEscape).join(","));
    for each (var row in rows) {
      var values = [];
      for each (var header in headers) {
        values.push(csvEscape(row[header]));
      }
      writer.println(values.join(","));
    }
  } finally {
    writer.close();
  }
}

function inc(map, key) {
  var current = map.get(key);
  map.put(key, current == null ? 1 : current + 1);
}

var bytes = readZipEntry(gephiPath, "Workspace_1_graphstore_bytes");
var model = GraphModelSerialization.read(new DataInputOutput(bytes));
var graph = model.getGraph();
var nodeTable = model.getNodeTable();
var edgeTable = model.getEdgeTable();
var nodeColumns = toJsArray(nodeTable);
var edgeColumns = toJsArray(edgeTable);

var outDirFile = new File(outputDir);
if (!outDirFile.exists()) {
  outDirFile.mkdirs();
}

var nodeRows = [];
var edgeRows = [];
var nodeTypeCounts = new LinkedHashMap();
var relCounts = new LinkedHashMap();

var nodeIterator = graph.getNodes().iterator();
while (nodeIterator.hasNext()) {
  var node = nodeIterator.next();
  var row = {
    id: node.getId(),
    label: node.getLabel(),
    store_id: node.getStoreId(),
    x: node.x(),
    y: node.y(),
    z: node.z(),
    size_gephi: node.size(),
    r: node.r(),
    g: node.g(),
    b: node.b(),
    alpha: node.alpha(),
    degree: graph.getDegree(node),
    indegree: graph.isDirected() ? graph.getInDegree(node) : graph.getDegree(node),
    outdegree: graph.isDirected() ? graph.getOutDegree(node) : graph.getDegree(node)
  };

  for each (var column in nodeColumns) {
    row[String(column.getId())] = node.getAttribute(column);
  }

  nodeRows.push(row);
  inc(nodeTypeCounts, String(row["d1"] || "Unknown"));
}

var edgeIterator = graph.getEdges().iterator();
while (edgeIterator.hasNext()) {
  var edge = edgeIterator.next();
  var row = {
    id: edge.getId(),
    source: edge.getSource().getId(),
    source_label: edge.getSource().getLabel(),
    target: edge.getTarget().getId(),
    target_label: edge.getTarget().getLabel(),
    weight: edge.getWeight(),
    directed: edge.isDirected()
  };

  for each (var edgeColumn in edgeColumns) {
    row[String(edgeColumn.getId())] = edge.getAttribute(edgeColumn);
  }

  edgeRows.push(row);
  inc(relCounts, String(row["d12"] || "unknown"));
}

var nodeHeaders = [
  "id",
  "label",
  "store_id",
  "x",
  "y",
  "z",
  "size_gephi",
  "r",
  "g",
  "b",
  "alpha",
  "degree",
  "indegree",
  "outdegree",
  "d1",
  "d2",
  "d3",
  "d4",
  "d5",
  "d6",
  "d7",
  "d8",
  "d10",
  "d11",
  "pageranks"
];

var edgeHeaders = [
  "id",
  "source",
  "source_label",
  "target",
  "target_label",
  "weight",
  "directed",
  "d12"
];

writeCsv(outputDir + "/nodes_full.csv", nodeHeaders, nodeRows);
writeCsv(outputDir + "/edges_full.csv", edgeHeaders, edgeRows);

var summaryRows = [
  { metric: "nodes_total", value: graph.getNodeCount() },
  { metric: "edges_total", value: graph.getEdgeCount() },
  { metric: "is_directed", value: graph.isDirected() },
  { metric: "node_table_columns", value: nodeColumns.length },
  { metric: "edge_table_columns", value: edgeColumns.length }
];

var nodeTypeKeys = nodeTypeCounts.keySet().toArray();
for each (var nodeType in nodeTypeKeys) {
  summaryRows.push({
    metric: "node_type_" + nodeType,
    value: nodeTypeCounts.get(nodeType)
  });
}

var relKeys = relCounts.keySet().toArray();
for each (var rel in relKeys) {
  summaryRows.push({
    metric: "relationship_" + rel,
    value: relCounts.get(rel)
  });
}

writeCsv(outputDir + "/summary_full.csv", ["metric", "value"], summaryRows);

print("Exported full Gephi graph");
print("nodes=" + graph.getNodeCount());
print("edges=" + graph.getEdgeCount());
print("output=" + outputDir);
