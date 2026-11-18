package ai.creatoros.smartclip

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Worker
import androidx.work.WorkerParameters

/** Sends a local reminder; it does not publish to social networks. */
class ScheduledPostReminderWorker(appContext: Context, params: WorkerParameters) : Worker(appContext, params) {
    override fun doWork(): Result {
        val platform = inputData.getString(KEY_PLATFORM)?.takeIf { it.isNotBlank() } ?: return Result.failure()
        val title = inputData.getString(KEY_TITLE)?.takeIf { it.isNotBlank() } ?: "Seu vídeo programado"
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(applicationContext, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) return Result.success()

        val manager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(NotificationChannel(
                CHANNEL_ID, "Lembretes de publicação", NotificationManager.IMPORTANCE_HIGH
            ).apply { description = "Avisos no horário configurado para publicar seus vídeos." })
        }
        val notificationId = (inputData.getString(KEY_ID) ?: id.toString()).hashCode() and 0x7fffffff
        val intent = Intent(applicationContext, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(applicationContext, notificationId, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_upload)
            .setContentTitle("Hora de publicar no $platform")
            .setContentText("$title está pronto. Abra o SMART CLIP para continuar.")
            .setStyle(NotificationCompat.BigTextStyle().bigText("$title está na sua programação do $platform. Abra o SMART CLIP e publique o vídeo na plataforma."))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
        NotificationManagerCompat.from(applicationContext).notify(notificationId, notification)
        return Result.success()
    }

    companion object {
        const val KEY_ID = "scheduled_id"
        const val KEY_PLATFORM = "platform"
        const val KEY_TITLE = "title"
        private const val CHANNEL_ID = "smart_clip_publication_reminders"
    }
}
