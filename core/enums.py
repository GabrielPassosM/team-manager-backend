from enum import Enum


class StageOptions(str, Enum):
    FASE_DE_GRUPOS = "fase_de_grupos"
    TRIANGULAR = "triangular"
    REPESCAGEM = "repescagem"
    DECIMA_SEXTAS_DE_FINAL = "decima_sextas_de_final"
    OITAVAS_DE_FINAL = "oitavas_de_final"
    QUARTAS_DE_FINAL = "quartas_de_final"
    SEMI_FINAL = "semi_final"
    FINAL = "final"
    VICE_CAMPEAO = "vice_campeao"
    CAMPEAO = "campeao"
