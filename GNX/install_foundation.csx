// GNX Foundation Installer v1.2
// Applies all GoblinNest Extender code + asset changes to data.win.
// Run via patcher.bat (UTMT CLI), or via G3M as a DATA patch (G3MTool).
//
// v1.2 = v1.1 (GML import + GNX_assets sprite import) + patch timing/diagnostics.
// Timing + a sprite-import summary are appended to
//   %LOCALAPPDATA%\goblin_nest\gnx_patch_timing.txt
// (ScriptMessage is suppressed under G3M, so the report goes to a file.)

using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Diagnostics;
using System.Threading.Tasks;
using UndertaleModLib.Util;
using ImageMagick;

var swTotal = Stopwatch.StartNew();

EnsureDataLoaded();

// Discover folders next to the script, next to the data file, or in cwd.
string?[] candidateDirs =
{
    !string.IsNullOrEmpty(ScriptPath) ? Path.GetDirectoryName(ScriptPath) : null,
    !string.IsNullOrEmpty(DataFilePath) ? Path.GetDirectoryName(DataFilePath) : null,
    Directory.GetCurrentDirectory()
};

// ── 1. GML Code Import ─────────────────────────────────────────────────

string? gmlDir = candidateDirs
    .Where(d => !string.IsNullOrEmpty(d))
    .Select(d => Path.Combine(d!, "gml"))
    .FirstOrDefault(Directory.Exists);

if (gmlDir == null)
    throw new Exception("GML folder not found. Checked next to the script, next to the data file, and the current directory.");

string[] gmlFiles = Directory.GetFiles(gmlDir!, "*.gml");
if (gmlFiles.Length == 0)
    throw new Exception($"No .gml files found in: {gmlDir}");

SetProgressBar(null, "GNX Foundation — Code", 0, gmlFiles.Length);
StartProgressBarUpdater();

long queueMs = 0, importMs = 0, totalBytes = 0;

await Task.Run(() =>
{
    var swQueue = Stopwatch.StartNew();

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
        totalBytes += code.Length;
        importGroup.QueueReplace(codeName, code);
        IncrementProgress();
    }

    swQueue.Stop();
    queueMs = swQueue.ElapsedMilliseconds;

    var swImport = Stopwatch.StartNew();
    importGroup.Import();       // all GML compilation + linking happens here
    swImport.Stop();
    importMs = swImport.ElapsedMilliseconds;
});

await StopProgressBarUpdater();
HideProgressBar();

// ── 2. GNX_assets Sprite Import ────────────────────────────────────────
// Imports every PNG in GNX_assets/ as a native sprite resource (spr_<filename>).
// Each sprite gets its own texture page. Origin is copied from the vanilla
// reference sprite when one exists (e.g. spr_option_window for gnx_option_window).
// In G3M, GNX_assets/ must be added alongside install_foundation.csx (not as
// an extra file), so it lands next to ScriptPath where candidateDirs finds it.

var swSprites = Stopwatch.StartNew();

string? assetsDir = candidateDirs
    .Where(d => !string.IsNullOrEmpty(d))
    .Select(d => Path.Combine(d!, "GNX_assets"))
    .FirstOrDefault(Directory.Exists);

int spriteCount = 0;
var spriteLog = new StringBuilder();
if (assetsDir != null)
{
    spriteLog.AppendLine($"  assets dir : {assetsDir}");
    string[] pngFiles = Directory.GetFiles(assetsDir, "*.png");
    int lastTexPage = Data.EmbeddedTextures.Count - 1;
    int lastTexItem = Data.TexturePageItems.Count - 1;

    foreach (string pngPath in pngFiles)
    {
        string baseName = Path.GetFileNameWithoutExtension(pngPath);
        string spriteName = "spr_" + baseName;

        // Skip if sprite already exists in data.win
        if (Data.Sprites.ByName(spriteName) != null)
        {
            spriteLog.AppendLine($"  skip {spriteName} (already present)");
            continue;
        }

        // Read image
        using MagickImage img = TextureWorker.ReadBGRAImageFromFile(pngPath);
        int w = (int)img.Width;
        int h = (int)img.Height;

        // Embedded texture (one per sprite, sized to the image)
        UndertaleEmbeddedTexture embTex = new();
        embTex.Name = new UndertaleString($"Texture {++lastTexPage}");
        embTex.TextureData.Image = GMImage.FromMagickImage(img).ConvertToPng();
        Data.EmbeddedTextures.Add(embTex);

        // Texture page item (full image, no trimming)
        UndertaleTexturePageItem tpi = new();
        tpi.Name = new UndertaleString($"PageItem {++lastTexItem}");
        tpi.SourceX = 0;            tpi.SourceY = 0;
        tpi.SourceWidth  = (ushort)w; tpi.SourceHeight  = (ushort)h;
        tpi.TargetX = 0;            tpi.TargetY = 0;
        tpi.TargetWidth  = (ushort)w; tpi.TargetHeight  = (ushort)h;
        tpi.BoundingWidth = (ushort)w; tpi.BoundingHeight = (ushort)h;
        tpi.TexturePage = embTex;
        Data.TexturePageItems.Add(tpi);

        // Origin: match the vanilla counterpart when one exists
        int ox = 0, oy = 0;
        if (baseName == "gnx_option_window")
        {
            UndertaleSprite refSpr = Data.Sprites.ByName("spr_option_window");
            if (refSpr != null) { ox = refSpr.OriginX; oy = refSpr.OriginY; }
        }

        // Create the sprite resource
        UndertaleSprite spr = new();
        spr.Name = Data.Strings.MakeString(spriteName);
        spr.Width  = (uint)w;
        spr.Height = (uint)h;
        spr.OriginX = ox;
        spr.OriginY = oy;
        spr.MarginLeft   = 0;
        spr.MarginRight  = w - 1;
        spr.MarginTop    = 0;
        spr.MarginBottom = h - 1;

        UndertaleSprite.TextureEntry texEntry = new();
        texEntry.Texture = tpi;
        spr.Textures.Add(texEntry);

        Data.Sprites.Add(spr);
        spriteCount++;
        spriteLog.AppendLine($"  added {spriteName} ({w}x{h} origin={ox},{oy})");
    }
}
else
{
    spriteLog.AppendLine("  assets dir : NOT FOUND (no sprites imported)");
}

swSprites.Stop();
swTotal.Stop();

// ── 3. Timing + sprite report ──────────────────────────────────────────
try
{
    var sb = new StringBuilder();
    sb.AppendLine($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] GNX patch (v1.2)");
    sb.AppendLine($"  files queued : {gmlFiles.Length}");
    sb.AppendLine($"  total GML     : {totalBytes / 1024} KB");
    sb.AppendLine($"  queue+read    : {queueMs} ms");
    sb.AppendLine($"  IMPORT/compile: {importMs} ms   <-- GML compile+link cost");
    sb.AppendLine($"  sprite import : {swSprites.ElapsedMilliseconds} ms, {spriteCount} added");
    sb.Append(spriteLog.ToString());
    sb.AppendLine($"  script total  : {swTotal.ElapsedMilliseconds} ms (excludes G3M data.win load before + save/xdelta after)");
    sb.AppendLine();

    string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
    string logDir = Path.Combine(localApp, "goblin_nest");
    Directory.CreateDirectory(logDir);
    File.AppendAllText(Path.Combine(logDir, "gnx_patch_timing.txt"), sb.ToString());
}
catch
{
    try
    {
        string fb = Path.Combine(Path.GetDirectoryName(gmlDir!)!, "gnx_patch_timing.txt");
        File.AppendAllText(fb, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] compile {importMs} ms, sprites {spriteCount}, total {swTotal.ElapsedMilliseconds} ms\n");
    }
    catch { /* best-effort */ }
}

ScriptMessage($"GNX Foundation v1.2 installed ({gmlFiles.Length} scripts patched, {spriteCount} sprites imported, compile {importMs} ms).");
