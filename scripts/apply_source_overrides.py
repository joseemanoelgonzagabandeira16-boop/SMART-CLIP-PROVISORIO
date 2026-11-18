#!/usr/bin/env python3
"""Applies maintained repository overrides to the Android project inside the source ZIP."""
from pathlib import Path
import shutil
import sys

project = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parent.parent
source = project / "app/src/main/java/ai/creatoros/smartclip/MainActivity.kt"
worker_target = project / "app/src/main/java/ai/creatoros/smartclip/ScheduledPostReminderWorker.kt"
worker_source = repo / "app/src/main/java/ai/creatoros/smartclip/ScheduledPostReminderWorker.kt"
gradle = project / "app/build.gradle.kts"
resource_source = repo / "app/src/main/res/xml/file_paths.xml"
resource_target = project / "app/src/main/res/xml/file_paths.xml"

if not source.is_file() or not gradle.is_file() or not worker_source.is_file() or not resource_source.is_file():
    raise SystemExit("Estrutura Android incompleta: não foi possível aplicar os ajustes do SMART CLIP.")
worker_target.parent.mkdir(parents=True, exist_ok=True)
resource_target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(worker_source, worker_target)
shutil.copy2(resource_source, resource_target)

gradle_text = gradle.read_text(encoding="utf-8")
dependency = '    implementation("androidx.work:work-runtime-ktx:2.10.0")'
if dependency not in gradle_text:
    anchor = '    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")'
    if anchor not in gradle_text:
        raise SystemExit("Não encontrei o bloco de dependências esperado no app/build.gradle.kts.")
    gradle.write_text(gradle_text.replace(anchor, anchor + "\n" + dependency, 1), encoding="utf-8")

text = source.read_text(encoding="utf-8")
transaction_anchor = """        val entries = read(context)
        val now = System.currentTimeMillis()"""
transaction_patch = """        val originalEntries = read(context)
        val entries = originalEntries.toMutableList()
        val now = System.currentTimeMillis()"""
if transaction_anchor in text:
    text = text.replace(transaction_anchor, transaction_patch, 1)
elif transaction_patch not in text:
    raise SystemExit("Não foi possível preparar rollback da fila.")
permission_anchor = "        super.onCreate(savedInstanceState)\n        window.statusBarColor"
permission_patch = """        super.onCreate(savedInstanceState)
        val notificationPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }
        if (android.os.Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermissionLauncher.launch(android.Manifest.permission.POST_NOTIFICATIONS)
        }
        window.statusBarColor"""
if "notificationPermissionLauncher" not in text:
    if permission_anchor not in text:
        raise SystemExit("Não encontrei o ponto de inicialização da MainActivity.")
    text = text.replace(permission_anchor, permission_patch, 1)

schedule_anchor = """            save(context, entries.sortedBy { it.scheduledAt })
        } catch (scheduleError: Exception) {"""
schedule_patch = """            save(context, entries.sortedBy { it.scheduledAt })
            createdFiles.forEachIndexed { index, _ ->
                val entry = entries[entries.size - orderedClips.size + index]
                val delay = (entry.scheduledAt - System.currentTimeMillis()).coerceAtLeast(0L)
                val request = androidx.work.OneTimeWorkRequestBuilder<ScheduledPostReminderWorker>()
                    .setInitialDelay(delay, java.util.concurrent.TimeUnit.MILLISECONDS)
                    .setInputData(androidx.work.workDataOf(
                        ScheduledPostReminderWorker.KEY_ID to entry.id,
                        ScheduledPostReminderWorker.KEY_PLATFORM to entry.platform,
                        ScheduledPostReminderWorker.KEY_TITLE to entry.title
                    ))
                    .addTag("smartclip-publication-reminder")
                    .build()
                androidx.work.WorkManager.getInstance(context).enqueueUniqueWork(
                    "smartclip-reminder-\u0024{entry.id}",
                    androidx.work.ExistingWorkPolicy.REPLACE,
                    request
                ).result.get(30, java.util.concurrent.TimeUnit.SECONDS)
            }
        } catch (scheduleError: Exception) {"""
if "OneTimeWorkRequestBuilder<ScheduledPostReminderWorker>" not in text:
    if schedule_anchor not in text:
        raise SystemExit("Não encontrei o ponto de gravação da fila de vídeos.")
    text = text.replace(schedule_anchor, schedule_patch, 1)

share_anchor = '                                Text("Salvo para programação", color = Color(0xFFFFD27A), fontSize = 10.sp)'
share_patch = """                                Text("Lembrete local aproximado • publicação manual no app da rede", color = Color(0xFFFFD27A), fontSize = 10.sp)
                                TextButton(onClick = {
                                    runCatching {
                                        val videoFile = java.io.File(entry.filePath)
                                        check(videoFile.isFile && videoFile.length() > 0L) { "O arquivo deste vídeo não está disponível." }
                                        val contentUri = androidx.core.content.FileProvider.getUriForFile(
                                            context, "${context.packageName}.fileprovider", videoFile
                                        )
                                        val shareIntent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                                            type = "video/mp4"
                                            putExtra(android.content.Intent.EXTRA_STREAM, contentUri)
                                            clipData = android.content.ClipData.newUri(context.contentResolver, entry.title, contentUri)
                                            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                        }
                                        context.startActivity(android.content.Intent.createChooser(shareIntent, "Compartilhar vídeo"))
                                    }.onFailure { error ->
                                        android.widget.Toast.makeText(context, error.message ?: "Não foi possível compartilhar o vídeo.", android.widget.Toast.LENGTH_LONG).show()
                                    }
                                }) {
                                    Text("COMPARTILHAR VÍDEO", color = Color(0xFF8DBBFF), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                }"""
if "COMPARTILHAR VÍDEO" not in text:
    if share_anchor not in text:
        raise SystemExit("Não encontrei o cartão de vídeos programados para inserir o compartilhamento.")
    text = text.replace(share_anchor, share_patch, 1)

rollback_anchor = "            createdFiles.forEach { runCatching { it.delete() } }"
rollback_patch = """            createdFiles.forEachIndexed { index, file ->
                val entryIndex = entries.size - orderedClips.size + index
                val failedEntry = entries.getOrNull(entryIndex)
                if (failedEntry != null) {
                    runCatching {
                        androidx.work.WorkManager.getInstance(context)
                            .cancelUniqueWork("smartclip-reminder-\u0024{failedEntry.id}")
                            .result.get(10, java.util.concurrent.TimeUnit.SECONDS)
                    }
                }
                runCatching { file.delete() }
            }
            runCatching { save(context, originalEntries) }"""
if rollback_anchor in text:
    text = text.replace(rollback_anchor, rollback_patch, 1)
elif "save(context, originalEntries)" not in text:
    raise SystemExit("Não foi possível preparar rollback dos lembretes.")
text = text.replace('Text("0", color = Color.White, fontSize = 88.sp', 'Text("—", color = Color.White, fontSize = 88.sp')
text = text.replace('Text("0", color = Color.White, fontSize = 22.sp', 'Text("—", color = Color.White, fontSize = 22.sp')
for label in ("INSCRITOS HOJE", "CURTIDAS", "COMENTÁRIOS", "VISUALIZAÇÕES"):
    text = text.replace(f'PerformanceMetric("♙", "{label}", "0"', f'PerformanceMetric("♙", "{label}", "—"')
text = text.replace('var refreshVersion by remember { mutableStateOf(0) }\n', '')
text = text.replace('.clickable { refreshVersion++ }\n', '')
text = text.replace('Text("ATUALIZAR", color = Color.White', 'Text("SEM DADOS CONECTADOS", color = Color.White')
source.write_text(text, encoding="utf-8")
print("Ajustes de lembrete e compartilhamento aplicados.")
