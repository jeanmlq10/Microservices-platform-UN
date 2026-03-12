function process(data) {
    const a = parseFloat(data.a) || 0;
    const b = parseFloat(data.b) || 0;
    return { a: a, b: b, sum: a + b, language: "Node.js" };
}
module.exports = process;
