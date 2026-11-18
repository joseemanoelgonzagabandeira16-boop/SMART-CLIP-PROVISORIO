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
    ("onAnalyze = { video, count, duration, useGemini, instructions ->",
     "onAnalyze = { video, count, duration, useGemini, instructions, verticalFormat ->"),
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


# SMART CLIP dual-mode implementation.
main = project / "app/src/main/java/ai/creatoros/smartclip/MainActivity.kt"
engine = project / "app/src/main/java/ai/creatoros/smartclip/VideoAnalysisEngine.kt"
main_text = main.read_text(encoding="utf-8")
engine_text = engine.read_text(encoding="utf-8")
adjust_start = main_text.index("private fun AdjustCutsScreen")
adjust_end = main_text.index("@UnstableApi", adjust_start)
adjust_text = main_text[adjust_start:adjust_end]

state_anchor = "    var useGemini by remember { mutableStateOf(false) }\n"
if "var cutsPerPlatform by remember" not in adjust_text:
    if state_anchor not in adjust_text:
        raise SystemExit("Não foi possível localizar o estado do modo de análise.")
    adjust_text = adjust_text.replace(state_anchor, state_anchor + "    var cutsPerPlatform by remember { mutableStateOf(3) }\n", 1)

txt_start_anchor = "            Column(\n                Modifier\n                    .fillMaxWidth()\n                    .clip(RoundedCornerShape(22.dp))"
summary_anchor = "            Column(\n                Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))"
format_anchor = "            Column(\n                Modifier\n                    .fillMaxWidth()\n                    .clip(RoundedCornerShape(28.dp))"
if "if (!useGemini) {" not in adjust_text:
    start = adjust_text.find(txt_start_anchor)
    summary = adjust_text.find(summary_anchor, start + 1)
    fmt = adjust_text.find(format_anchor, summary + 1)
    if min(start, summary, fmt) < 0:
        raise SystemExit("Não foi possível delimitar a área de importação TXT.")
    block = adjust_text[start:fmt]
    block = "".join(("    " + line if line.strip() else line) for line in block.splitlines(keepends=True))
    adjust_text = adjust_text[:start] + "            if (!useGemini) {\n" + block + "            }\n\n" + adjust_text[fmt:]

adjust_text = adjust_text.replace('Text("MODO DE ANÁLISE", color = Color.White, fontSize = 15.sp, fontWeight = FontWeight.Bold)',
                                  'Text("MODO DE CRIAÇÃO", color = Color.White, fontSize = 15.sp, fontWeight = FontWeight.Bold)', 1)
adjust_text = adjust_text.replace('label = "SEM GEMINI"', 'label = "ARQUIVO TXT"', 1)
adjust_text = adjust_text.replace('label = "COM GEMINI"', 'label = "COM IA"', 1)
old_ai_sentence = "O Gemini pode analisar visualmente o vídeo, mas os horários INICIO e FIM do TXT são obrigatórios e nunca serão alterados."
old_txt_sentence = "O aplicativo usa diretamente os horários INICIO e FIM do TXT, sem enviar o vídeo para uma API. Não gera legendas."
main_text = main_text.replace(old_ai_sentence, "A IA analisa o vídeo inteiro, identifica os melhores momentos e cria os horários, títulos, descrições e hashtags. Não precisa de TXT.", 1)
main_text = main_text.replace(old_txt_sentence, "O modo manual usa exclusivamente os horários e metadados definidos no arquivo TXT. Nenhuma IA é utilizada.", 1)
if "O Gemini pode analisar visualmente o vídeo" in main_text:
    raise SystemExit("Não foi possível atualizar a explicação dos modos.")

ai_controls_anchor = format_anchor
ai_controls = '''            if (useGemini) {
                Column(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp))
                        .background(Color(0xFF102B52)).padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text("QUANTIDADE DE CORTES POR REDE", color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center) {
                        FormatOption(modifier = Modifier.weight(1f), label = "−", selected = false) {
                            cutsPerPlatform = (cutsPerPlatform - 1).coerceAtLeast(1)
                        }
                        Text(cutsPerPlatform.toString(), color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.ExtraBold,
                            modifier = Modifier.weight(1f), textAlign = TextAlign.Center)
                        FormatOption(modifier = Modifier.weight(1f), label = "+", selected = false) {
                            cutsPerPlatform = (cutsPerPlatform + 1).coerceAtMost(30)
                        }
                    }
                    Text("A IA criará " + cutsPerPlatform + " cortes para cada rede (YouTube, Instagram e TikTok), totalizando " + (cutsPerPlatform * 3) + ".",
                        color = Color(0xFFAFC2E8), fontSize = 12.sp)
                }
            }

'''
if "QUANTIDADE DE CORTES POR REDE" not in adjust_text:
    if ai_controls_anchor not in adjust_text:
        raise SystemExit("Não foi possível inserir o seletor de quantidade para IA.")
    adjust_text = adjust_text.replace(ai_controls_anchor, ai_controls + ai_controls_anchor, 1)

old_click = '''                        } else if (customInstructions.isBlank()) {
                            android.widget.Toast.makeText(context, "Envie um novo arquivo .txt com as instruções desta edição.", android.widget.Toast.LENGTH_LONG).show()
                        } else {
                            val cutsPerPlatform = runCatching {
                                VideoAnalysisEngine.getCutsPerPlatform(customInstructions)
                            }.getOrElse { error ->
                                android.widget.Toast.makeText(context, error.message ?: "Confira a estrutura do arquivo .TXT.", android.widget.Toast.LENGTH_LONG).show()
                                return@clickable
                            }
                            selectedVideo?.let { onAnalyze(it, cutsPerPlatform, clipDuration, useGemini, customInstructions, verticalFormat) }
                        }'''
new_click = '''                        } else if (useGemini) {
                            selectedVideo?.let { onAnalyze(it, cutsPerPlatform, clipDuration, true, "", verticalFormat) }
                        } else if (customInstructions.isBlank()) {
                            android.widget.Toast.makeText(context, "No modo TXT, importe o arquivo de instruções antes de continuar.", android.widget.Toast.LENGTH_LONG).show()
                        } else {
                            val txtCutCount = runCatching {
                                VideoAnalysisEngine.getCutsPerPlatform(customInstructions)
                            }.getOrElse { error ->
                                android.widget.Toast.makeText(context, error.message ?: "Confira a estrutura do arquivo .TXT.", android.widget.Toast.LENGTH_LONG).show()
                                return@clickable
                            }
                            selectedVideo?.let { onAnalyze(it, txtCutCount, clipDuration, false, customInstructions, verticalFormat) }
                        }'''
if old_click in adjust_text:
    adjust_text = adjust_text.replace(old_click, new_click, 1)
elif "No modo TXT, importe o arquivo de instruções" not in adjust_text:
    raise SystemExit("Não foi possível separar a ação de análise dos dois modos.")

adjust_text = adjust_text.replace('Text("ANALISAR", color = Color.White, fontSize = 24.sp',
                                  'Text(if (useGemini) "ANALISAR COM IA" else "GERAR CORTES DO TXT", color = Color.White, fontSize = 20.sp', 1)
main_text = main_text[:adjust_start] + adjust_text + main_text[adjust_end:]
main.write_text(main_text, encoding="utf-8")

old_validation = "        validateInstructionScript(context, videoUri, customInstructions)\n"
if old_validation in engine_text:
    engine_text = engine_text.replace(old_validation,
        "        if (customInstructions.isNotBlank()) validateInstructionScript(context, videoUri, customInstructions)\n", 1)

old_return = '            return requestSuggestions(file.getString("uri"), file.optString("mimeType", mimeType), apiKey, requestedCount, requestedDurationSeconds, customInstructions, availableModels, onStatus)'
new_return = '''            val uploadedUri = file.getString("uri")
            val uploadedMimeType = file.optString("mimeType", mimeType)
            return if (customInstructions.isBlank()) {
                requestAiSuggestions(uploadedUri, uploadedMimeType, apiKey, requestedCount, requestedDurationSeconds,
                    getVideoDurationMs(context, videoUri), availableModels, onStatus)
            } else {
                requestSuggestions(uploadedUri, uploadedMimeType, apiKey, requestedCount, requestedDurationSeconds,
                    customInstructions, availableModels, onStatus)
            }'''
if old_return in engine_text:
    engine_text = engine_text.replace(old_return, new_return, 1)
elif "requestAiSuggestions(uploadedUri" not in engine_text:
    raise SystemExit("Não foi possível conectar o modo IA independente do TXT.")

ai_function = r'''
    /** Analisa o vídeo sem TXT e cria horários e metadados inteiramente com IA. */
    private fun requestAiSuggestions(
        fileUri: String,
        mimeType: String,
        apiKey: String,
        requestedCount: Int,
        requestedDurationSeconds: Int,
        videoDurationMs: Long,
        models: List<String>,
        onStatus: (String) -> Unit
    ): List<SmartClipSuggestion> {
        require(requestedCount in 1..30) { "Escolha entre 1 e 30 cortes por rede." }
        val total = requestedCount * 3
        val durationRule = if (requestedDurationSeconds > 0) {
            "Tente manter cada corte próximo de " + requestedDurationSeconds + " segundos."
        } else {
            "Prefira cortes curtos e completos, geralmente entre 20 e 60 segundos, sem ultrapassar a duração do vídeo."
        }
        val prompt = """
            Você é o editor inteligente do SMART CLIP. Analise o vídeo inteiro e selecione os melhores momentos
            que tenham contexto, começo e fim compreensíveis, boa clareza e potencial de interesse.
            Crie exatamente $requestedCount cortes para cada plataforma: YouTube, Instagram e TikTok.
            Total obrigatório: $total cortes. Duração total do vídeo: $videoDurationMs milissegundos.
            $durationRule
            Escolha intervalos diferentes dentro do vídeo quando houver conteúdo suficiente. Não crie cortes fora do vídeo.
            Para cada corte, gere início e fim em milissegundos inteiros (start_ms e end_ms), título (até 100 caracteres),
            descrição e hashtags relevantes. Adapte título, descrição e hashtags ao estilo da plataforma.
            YouTube deve vir primeiro, depois Instagram e por último TikTok. Dentro de cada rede, numere os cortes
            na ordem cronológica em que aparecem no vídeo.
            Não invente fatos sobre o conteúdo. Não inclua legendas/transcrição nem texto sobreposto no vídeo.
            Retorne SOMENTE JSON válido, sem markdown, neste formato:
            {"clips":[{"platform":"YouTube","start_ms":1000,"end_ms":25000,"title":"Título","description":"Descrição","hashtags":"#tema #assunto"}]}
            O array deve conter exatamente $total objetos, com exatamente $requestedCount para cada plataforma.
        """.trimIndent()
        val parts = JSONArray()
            .put(JSONObject().put("text", prompt))
            .put(JSONObject().put("file_data", JSONObject().put("mime_type", mimeType).put("file_uri", fileUri)))
        val body = JSONObject()
            .put("contents", JSONArray().put(JSONObject().put("parts", parts)))
            .put("generationConfig", JSONObject().put("responseMimeType", "application/json"))
        val (_, responseText) = generateWithFallback(apiKey, body, models) { model ->
            onStatus("IA analisando o vídeo com " + model + "...")
        }
        val response = JSONObject(responseText)
        val candidates = response.optJSONArray("candidates") ?: JSONArray()
        val candidate = candidates.optJSONObject(0)
        val generated = candidate?.optJSONObject("content")?.optJSONArray("parts")
            ?.let { responseParts ->
                (0 until responseParts.length()).mapNotNull { index ->
                    responseParts.optJSONObject(index)?.optString("text")?.takeIf { it.isNotBlank() }
                }.joinToString("\n")
            }.orEmpty()
        if (generated.isBlank()) {
            val blockReason = response.optJSONObject("promptFeedback")?.optString("blockReason").orEmpty()
            val finishReason = candidate?.optString("finishReason").orEmpty()
            error("A IA não retornou cortes utilizáveis. " + blockReason.ifBlank { finishReason }.ifBlank { "Resposta vazia" })
        }
        var jsonText = generated.trim()
        val fence = 96.toChar().toString().repeat(3)
        jsonText = jsonText.removePrefix(fence + "json").removePrefix(fence).removeSuffix(fence).trim()
        val jsonStart = jsonText.indexOf('{')
        val jsonEnd = jsonText.lastIndexOf('}')
        if (jsonStart >= 0 && jsonEnd > jsonStart) jsonText = jsonText.substring(jsonStart, jsonEnd + 1)
        val clips = runCatching { JSONObject(jsonText).getJSONArray("clips") }
            .getOrElse { error("A IA respondeu, mas o formato dos cortes veio inválido. Tente novamente.") }
        require(clips.length() == total) {
            "A IA retornou " + clips.length() + " cortes; eram esperados " + total + ". Tente analisar novamente."
        }

        val platformOrder = listOf("YouTube", "Instagram", "TikTok")
        val perPlatform = platformOrder.associateWith { mutableListOf<SmartClipSuggestion>() }
        val seenIntervals = mutableSetOf<String>()
        for (index in 0 until clips.length()) {
            val item = clips.optJSONObject(index) ?: error("O corte " + (index + 1) + " veio em formato inválido.")
            val platformRaw = item.optString("platform").trim()
            val platform = platformOrder.firstOrNull { it.equals(platformRaw, ignoreCase = true) }
                ?: error("A IA informou uma plataforma inválida no corte " + (index + 1) + ".")
            val startMs = item.optLong("start_ms", -1L)
            val endMs = item.optLong("end_ms", -1L)
            require(startMs >= 0L && endMs - startMs >= 1000L && endMs <= videoDurationMs) {
                "A IA sugeriu horários inválidos no corte " + (index + 1) + ". Tente novamente."
            }
            val signature = platform.lowercase(Locale.ROOT) + ":" + startMs + ":" + endMs
            require(seenIntervals.add(signature)) {
                "A IA repetiu um intervalo na plataforma " + platform + ". Tente analisar novamente."
            }
            val title = item.optString("title").trim()
            val description = item.optString("description").trim()
            val hashtags = item.optString("hashtags").trim()
            require(title.isNotBlank() && title.length <= 100) {
                "A IA gerou um título vazio ou maior que 100 caracteres no corte " + (index + 1) + "."
            }
            val combinedText = listOf(description, hashtags).filter { it.isNotBlank() }.joinToString("\n\n")
            val maxDescription = if (platform == "YouTube") 5000 else 500
            require(combinedText.length <= maxDescription) {
                "A descrição do corte " + (index + 1) + " excede o limite da plataforma " + platform + "."
            }
            perPlatform.getValue(platform).add(
                SmartClipSuggestion(platform, title, combinedText, "", startMs, endMs)
            )
        }
        platformOrder.forEach { platform ->
            require(perPlatform.getValue(platform).size == requestedCount) {
                "A IA não gerou exatamente " + requestedCount + " cortes para " + platform + ". Tente novamente."
            }
        }
        return platformOrder.flatMap { platform ->
            perPlatform.getValue(platform).sortedBy { it.startMs }
        }
    }

'''
function_anchor = "    private fun deleteUploadedFile(name: String, apiKey: String) {"
if "private fun requestAiSuggestions(" not in engine_text:
    if function_anchor not in engine_text:
        raise SystemExit("Não foi possível inserir o gerador de cortes por IA.")
    engine_text = engine_text.replace(function_anchor, ai_function + function_anchor, 1)

engine.write_text(engine_text, encoding="utf-8")
print("Modos IA independente e TXT manual aplicados.")
