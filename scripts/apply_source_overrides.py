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

if not source.is_file() or not gradle.is_file() or not worker_source.is_file():
    raise SystemExit("Estrutura Android incompleta: não foi possível aplicar os ajustes do SMART CLIP.")
shutil.copy2(worker_source, worker_target)

gradle_text = gradle.read_text(encoding="utf-8")
dependency = '    implementation("androidx.work:work-runtime-ktx:2.10.0")'
if dependency not in gradle_text:
    anchor = '    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")'
    if anchor not in gradle_text:
        raise SystemExit("Não encontrei o bloco de dependências esperado no app/build.gradle.kts.")
    gradle.write_text(gradle_text.replace(anchor, anchor + "\n" + dependency, 1), encoding="utf-8")

text = source.read_text(encoding="utf-8")
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
                runCatching {
                    androidx.work.WorkManager.getInstance(context).enqueueUniqueWork(
                        "smartclip-reminder-\u0024{entry.id}",
                        androidx.work.ExistingWorkPolicy.REPLACE,
                        request
                    )
                }
            }
        } catch (scheduleError: Exception) {"""
if "OneTimeWorkRequestBuilder<ScheduledPostReminderWorker>" not in text:
    if schedule_anchor not in text:
        raise SystemExit("Não encontrei o ponto de gravação da fila de vídeos.")
    text = text.replace(schedule_anchor, schedule_patch, 1)
text = text.replace("Salvo para programação", "Lembrete local aproximado • publicação manual no app da rede")
source.write_text(text, encoding="utf-8")
print("Ajustes de lembretes aplicados.")
