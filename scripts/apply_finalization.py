#!/usr/bin/env python3
"""Finalizes portrait export and adds focused TXT parser unit tests."""
from pathlib import Path
import shutil
import sys

project = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parent.parent
main = project / "app/src/main/java/ai/creatoros/smartclip/MainActivity.kt"
engine = project / "app/src/main/java/ai/creatoros/smartclip/VideoAnalysisEngine.kt"
gradle = project / "app/build.gradle.kts"
tests_src = repo / "app/src/test/java/ai/creatoros/smartclip/VideoAnalysisEngineTest.kt"
tests_dst = project / "app/src/test/java/ai/creatoros/smartclip/VideoAnalysisEngineTest.kt"
for path in (main, engine, gradle, tests_src):
    if not path.is_file():
        raise SystemExit(f"Arquivo necessário ausente: {path}")

text = main.read_text(encoding="utf-8")
changes = [
    ("    var analysisUseGemini by remember { mutableStateOf(false) }\n",
     "    var analysisUseGemini by remember { mutableStateOf(false) }\n    var analysisVerticalFormat by remember { mutableStateOf(false) }\n"),
    ("                analysisUseGemini = useGemini\n                analysisCustomInstructions = instructions",
     "                analysisUseGemini = useGemini\n                analysisVerticalFormat = verticalFormat\n                analysisCustomInstructions = instructions"),
    ("            useGemini = analysisUseGemini,\n            customInstructions",
     "            useGemini = analysisUseGemini,\n            verticalFormat = analysisVerticalFormat,\n            customInstructions"),
    ("private fun AdjustCutsScreen(onBack: () -> Unit, onAnalyze: (android.net.Uri?, Int, Int, Boolean, String) -> Unit)",
     "private fun AdjustCutsScreen(onBack: () -> Unit, onAnalyze: (android.net.Uri?, Int, Int, Boolean, String, Boolean) -> Unit)"),
    ("onAnalyze(it, cutsPerPlatform, clipDuration, useGemini, customInstructions)",
     "onAnalyze(it, cutsPerPlatform, clipDuration, useGemini, customInstructions, verticalFormat)"),
    ("    useGemini: Boolean,\n    customInstructions: String,\n    onBack: () -> Unit,",
     "    useGemini: Boolean,\n    verticalFormat: Boolean,\n    customInstructions: String,\n    onBack: () -> Unit,"),
    ("VideoCutEngine.cut(context, videoUri, suggestion, index)",
     "VideoCutEngine.cut(context, videoUri, suggestion, index, verticalFormat)"),
]
for old, new in changes:
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("Não foi possível conectar a seleção 9:16 à exportação: " + old[:90])
main.write_text(text, encoding="utf-8")

code = engine.read_text(encoding="utf-8")
old_sig = "fun cut(context: Context, sourceUri: Uri, suggestion: SmartClipSuggestion, index: Int): File {"
new_sig = "fun cut(context: Context, sourceUri: Uri, suggestion: SmartClipSuggestion, index: Int, verticalFormat: Boolean = false): File {"
if old_sig in code:
    code = code.replace(old_sig, new_sig, 1)
elif new_sig not in code:
    raise SystemExit("Assinatura de VideoCutEngine.cut não encontrada.")
old_start = "                transformer.start(mediaItem, output.absolutePath)"
new_start = """                val exportItem = if (verticalFormat) {
                    val portrait = androidx.media3.effect.Presentation.createForWidthAndHeight(
                        1080, 1920, androidx.media3.effect.Presentation.LAYOUT_SCALE_TO_FIT_WITH_CROP
                    )
                    androidx.media3.transformer.EditedMediaItem.Builder(mediaItem)
                        .setEffects(androidx.media3.transformer.Effects(emptyList(), listOf(portrait)))
                        .build()
                } else {
                    androidx.media3.transformer.EditedMediaItem.Builder(mediaItem).build()
                }
                transformer.start(exportItem, output.absolutePath)"""
if old_start in code:
    code = code.replace(old_start, new_start, 1)
elif "Presentation.createForWidthAndHeight" not in code:
    raise SystemExit("Chamada de exportação Media3 não encontrada.")
engine.write_text(code, encoding="utf-8")

gradle_text = gradle.read_text(encoding="utf-8")
if 'testImplementation("junit:junit:4.13.2")' not in gradle_text:
    anchor = '    implementation("com.google.guava:guava:33.3.1-android")'
    if anchor not in gradle_text:
        raise SystemExit("Não foi possível localizar as dependências para adicionar JUnit.")
    gradle_text = gradle_text.replace(anchor, anchor + '\n    testImplementation("junit:junit:4.13.2")', 1)
gradle.write_text(gradle_text, encoding="utf-8")
tests_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(tests_src, tests_dst)
print("Formato 9:16 ligado à exportação e testes do parser TXT adicionados.")
