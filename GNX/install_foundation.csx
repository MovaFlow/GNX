// GNX Foundation Installer v1.0
// Applies all GoblinNest Extender code changes to data.win.
// Run via patcher.bat (UTMT CLI), or via G3M as a DATA patch (G3MTool).

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UndertaleModLib.Util;

EnsureDataLoaded();

// Look for a "gml" folder next to the script (UTMT CLI / patcher.bat layout),
// next to the data file being patched (G3M layout), or in the current directory.
string?[] candidateDirs =
{
    !string.IsNullOrEmpty(ScriptPath) ? Path.GetDirectoryName(ScriptPath) : null,
    !string.IsNullOrEmpty(DataFilePath) ? Path.GetDirectoryName(DataFilePath) : null,
    Directory.GetCurrentDirectory()
};

string? gmlDir = candidateDirs
    .Where(d => !string.IsNullOrEmpty(d))
    .Select(d => Path.Combine(d!, "gml"))
    .FirstOrDefault(Directory.Exists);

if (gmlDir == null)
    throw new Exception("GML folder not found. Checked next to the script, next to the data file, and the current directory.");

string[] gmlFiles = Directory.GetFiles(gmlDir!, "*.gml");
if (gmlFiles.Length == 0)
    throw new Exception($"No .gml files found in: {gmlDir}");

SetProgressBar(null, "GNX Foundation", 0, gmlFiles.Length);
StartProgressBarUpdater();

await Task.Run(() =>
{
    var importGroup = new UndertaleModLib.Compiler.CodeImportGroup(Data)
    {
        AutoCreateAssets = true
    };

    foreach (string file in gmlFiles)
    {
        string code = File.ReadAllText(file);
        // Inline the GNX_LOG macro — UTMT cross-script macro resolution is unreliable
        code = code.Replace("GNX_LOG", "\"gnx_debug.txt\"");
        string codeName = Path.GetFileNameWithoutExtension(file);
        // Skip s_macro — macros are now inlined, no script entry needed
        if (codeName == "gml_GlobalScript_s_macro") { IncrementProgress(); continue; }
        importGroup.QueueReplace(codeName, code);
        IncrementProgress();
    }

    importGroup.Import();
});

await StopProgressBarUpdater();
HideProgressBar();
ScriptMessage($"GNX Foundation v1.0 installed ({gmlFiles.Length} scripts patched).");
