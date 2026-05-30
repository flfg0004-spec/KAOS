// QuickAdd macro para añadir note actual a library/archive
// Copia de respaldo desde .obsidian/quickadd/macros/
module.exports = async (params) => {
    const app = params.app;
    const activeFile = app.workspace.getActiveFile();
    if (!activeFile) return;

    const content = await app.vault.read(activeFile);

    // Add audience: both y library: true al frontmatter
    const updated = content.replace(/^---\n/, '---\naudience: both\nlibrary: true\n');
    await app.vault.modify(activeFile, updated);

    new Notice(`✅ Marked for library: ${activeFile.name}`);
};
