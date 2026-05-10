(function () {
  function mojibakeCount(text) {
    return (String(text).match(/[ÃÂâ]/g) || []).length;
  }

  function repairText(value) {
    if (typeof value !== "string") return value;
    const text = value.trim();
    if (!text) return value;

    const originalCount = mojibakeCount(text);
    if (!originalCount) return value;

    try {
      const bytes = Uint8Array.from(Array.from(text, (char) => char.charCodeAt(0) & 0xff));
      const candidate = new TextDecoder("utf-8").decode(bytes);
      if (candidate && mojibakeCount(candidate) < originalCount) {
        return candidate;
      }
    } catch (_) {
      return value;
    }

    return value;
  }

  function deepRepairData(input, seen = new WeakSet()) {
    if (input === null || input === undefined) return input;
    if (typeof input === "string") return repairText(input);
    if (typeof input !== "object") return input;
    if (seen.has(input)) return input;
    seen.add(input);

    if (Array.isArray(input)) {
      for (let i = 0; i < input.length; i += 1) {
        input[i] = deepRepairData(input[i], seen);
      }
      return input;
    }

    Object.keys(input).forEach((key) => {
      input[key] = deepRepairData(input[key], seen);
    });
    return input;
  }

  window.repairText = repairText;
  window.deepRepairData = deepRepairData;
})();
