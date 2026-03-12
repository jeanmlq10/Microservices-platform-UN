function process(data) {
    const name = data.name || "Mundo";
    return { message: `Hola ${name}!`, language: "Node.js" };
}
module.exports = process;
