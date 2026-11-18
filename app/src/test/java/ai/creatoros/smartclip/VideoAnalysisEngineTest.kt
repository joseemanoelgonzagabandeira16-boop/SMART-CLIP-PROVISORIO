package ai.creatoros.smartclip

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class VideoAnalysisEngineTest {
    private val validScript = """
        QUANTIDADE_DE_CORTES: 1

        [CORTE 01]
        PLATAFORMA: YouTube
        INICIO: 00:00
        FIM: 00:12
        TITULO: Corte do YouTube
        DESCRICAO: Descrição do vídeo para YouTube.
        HASHTAGS: #youtube

        [CORTE 01]
        PLATAFORMA: Instagram
        INICIO: 00:12
        FIM: 00:24
        TITULO: Corte do Instagram
        DESCRICAO: Descrição do vídeo para Instagram.
        HASHTAGS: #instagram

        [CORTE 01]
        PLATAFORMA: TikTok
        INICIO: 00:24
        FIM: 00:36
        TITULO: Corte do TikTok
        DESCRICAO: Descrição do vídeo para TikTok.
        HASHTAGS: #tiktok
    """.trimIndent()

    @Test
    fun acceptsOneCompleteCutForEachPlatform() {
        assertEquals(1, VideoAnalysisEngine.getCutsPerPlatform(validScript))
    }

    @Test
    fun rejectsMissingPlatformCut() {
        val incomplete = validScript.substringBefore("[CORTE 01]\nPLATAFORMA: TikTok")
        assertThrows(IllegalArgumentException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(incomplete)
        }
    }

    @Test
    fun rejectsInvalidCutCount() {
        val invalid = validScript.replace("QUANTIDADE_DE_CORTES: 1", "QUANTIDADE_DE_CORTES: 0")
        assertThrows(IllegalArgumentException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(invalid)
        }
    }

    @Test
    fun rejectsInvalidPlatformName() {
        val invalid = validScript.replace("PLATAFORMA: TikTok", "PLATAFORMA: OutraRede")
        assertThrows(IllegalStateException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(invalid)
        }
    }
}
