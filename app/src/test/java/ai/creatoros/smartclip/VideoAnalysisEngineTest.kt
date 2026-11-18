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
    @Test
    fun acceptsTwoCutsPerPlatform() {
        val secondBatch = """
            
            [CORTE 02]
            PLATAFORMA: YouTube
            INICIO: 00:36
            FIM: 00:48
            TITULO: Segundo corte YouTube
            DESCRICAO: Segunda descrição.
            HASHTAGS: #youtube

            [CORTE 02]
            PLATAFORMA: Instagram
            INICIO: 00:48
            FIM: 01:00
            TITULO: Segundo corte Instagram
            DESCRICAO: Segunda descrição.
            HASHTAGS: #instagram

            [CORTE 02]
            PLATAFORMA: TikTok
            INICIO: 01:00
            FIM: 01:12
            TITULO: Segundo corte TikTok
            DESCRICAO: Segunda descrição.
            HASHTAGS: #tiktok
        """.trimIndent()
        val script = validScript.replace("QUANTIDADE_DE_CORTES: 1", "QUANTIDADE_DE_CORTES: 2") + "\n\n" + secondBatch
        assertEquals(2, VideoAnalysisEngine.getCutsPerPlatform(script))
    }

    @Test
    fun rejectsDuplicateCutNumberWithinSamePlatform() {
        val invalid = validScript.replace("PLATAFORMA: Instagram", "PLATAFORMA: YouTube")
        assertThrows(IllegalArgumentException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(invalid)
        }
    }

    @Test
    fun rejectsMissingHashtagsField() {
        val invalid = validScript.replace("        HASHTAGS: #tiktok", "")
        assertThrows(IllegalArgumentException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(invalid)
        }
    }

    @Test
    fun rejectsEndTimeBeforeStartTime() {
        val invalid = validScript.replace("FIM: 00:12", "FIM: 00:00")
        assertThrows(IllegalArgumentException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(invalid)
        }
    }

    @Test
    fun rejectsTitleLongerThanOneHundredCharacters() {
        val invalid = validScript.replace("TITULO: Corte do YouTube", "TITULO: " + "A".repeat(101))
        assertThrows(IllegalArgumentException::class.java) {
            VideoAnalysisEngine.getCutsPerPlatform(invalid)
        }
    }

}
