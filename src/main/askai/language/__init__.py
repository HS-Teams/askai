# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.language
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .language import AF_ZA
    from .ai_translator import AITranslator
    from .language import AR_AE
    from .language import AR_BH
    from .language import AR_DZ
    from .language import AR_EG
    from .language import AR_IQ
    from .language import AR_JO
    from .language import AR_KW
    from .language import AR_LY
    from .language import AR_MA
    from .language import AR_OM
    from .language import AR_QA
    from .language import AR_SA
    from .language import AR_TN
    from .language import AR_YE
    from .language import AS_IN
    from .language import AZ_AZ
    from .translators.argos_translator import ArgosTranslator
    from .language import BE_BY
    from .language import BG_BG
    from .language import BN_IN
    from .language import BS_BA
    from .language import C
    from .language import CA_ES
    from .language import CS_CZ
    from .language import DA_DK
    from .language import DE_AT
    from .language import DE_BE
    from .language import DE_CH
    from .language import DE_DE
    from .language import DE_LI
    from .language import DE_LU
    from .translators.deepl_translator import DeepLTranslator
    from .language import EL_CY
    from .language import EL_GR
    from .language import EN_AU
    from .language import EN_BW
    from .language import EN_CA
    from .language import EN_GB
    from .language import EN_HK
    from .language import EN_IE
    from .language import EN_IN
    from .language import EN_MT
    from .language import EN_NZ
    from .language import EN_PH
    from .language import EN_SG
    from .language import EN_US
    from .language import EN_ZW
    from .language import ES_AR
    from .language import ES_BO
    from .language import ES_CL
    from .language import ES_CO
    from .language import ES_CR
    from .language import ES_DO
    from .language import ES_EC
    from .language import ES_ES
    from .language import ES_GT
    from .language import ES_HN
    from .language import ES_MX
    from .language import ES_NI
    from .language import ES_PA
    from .language import ES_PE
    from .language import ES_PR
    from .language import ES_PY
    from .language import ES_SV
    from .language import ES_US
    from .language import ES_UY
    from .language import ES_VE
    from .language import ET_EE
    from .language import FI_FI
    from .language import FR_BE
    from .language import FR_CA
    from .language import FR_CH
    from .language import FR_FR
    from .language import FR_LU
    from .language import GU_IN
    from .language import HE_IL
    from .language import HI_IN
    from .language import HR_HR
    from .language import HU_HU
    from .language import HY_AM
    from .language import ID_ID
    from .language import IS_IS
    from .language import IT_CH
    from .language import IT_IT
    from .language import JA_JP
    from .language import KA_GE
    from .language import KK_KZ
    from .language import KN_IN
    from .language import KO_KR
    from .language import KS_IN
    from .language import KU_TR
    from .language import KY_KG
    from .language import LT_LT
    from .language import LV_LV
    from .language import Language
    from .detection import MINIMUM_LANGUAGE_DISTANCE
    from .language import MK_MK
    from .language import ML_IN
    from .translators.marian_translator import MODEL_NAME
    from .language import MR_IN
    from .language import MS_MY
    from .language import MT_MT
    from .translators.marian_translator import MarianTranslator
    from .language import NB_NO
    from .language import NL_BE
    from .language import NL_NL
    from .language import NN_NO
    from .detection import NON_PROSE
    from .language import OR_IN
    from .language import PA_IN
    from .language import PL_PL
    from .language import PT_BR
    from .language import PT_PT
    from .language import RO_RO
    from .language import RU_RU
    from .language import RU_UA
    from .language import SA_IN
    from .language import SK_SK
    from .language import SL_SI
    from .language import SQ_AL
    from .language import SR_ME
    from .language import SR_RS
    from .language import SV_SE
    from .language import TA_IN
    from .language import TE_IN
    from .language import TH_TH
    from .language import TR_TR
    from .language import UK_UA
    from .language import VI_VN
    from .language import ZH_CN
    from .language import ZH_HK
    from .language import ZH_SG
    from .language import ZH_TW


_EXPORTS = {
    'AF_ZA': ('language', 'AF_ZA'),
    'AITranslator': ('ai_translator', 'AITranslator'),
    'AR_AE': ('language', 'AR_AE'),
    'AR_BH': ('language', 'AR_BH'),
    'AR_DZ': ('language', 'AR_DZ'),
    'AR_EG': ('language', 'AR_EG'),
    'AR_IQ': ('language', 'AR_IQ'),
    'AR_JO': ('language', 'AR_JO'),
    'AR_KW': ('language', 'AR_KW'),
    'AR_LY': ('language', 'AR_LY'),
    'AR_MA': ('language', 'AR_MA'),
    'AR_OM': ('language', 'AR_OM'),
    'AR_QA': ('language', 'AR_QA'),
    'AR_SA': ('language', 'AR_SA'),
    'AR_TN': ('language', 'AR_TN'),
    'AR_YE': ('language', 'AR_YE'),
    'AS_IN': ('language', 'AS_IN'),
    'AZ_AZ': ('language', 'AZ_AZ'),
    'ArgosTranslator': ('translators.argos_translator', 'ArgosTranslator'),
    'BE_BY': ('language', 'BE_BY'),
    'BG_BG': ('language', 'BG_BG'),
    'BN_IN': ('language', 'BN_IN'),
    'BS_BA': ('language', 'BS_BA'),
    'C': ('language', 'C'),
    'CA_ES': ('language', 'CA_ES'),
    'CS_CZ': ('language', 'CS_CZ'),
    'DA_DK': ('language', 'DA_DK'),
    'DE_AT': ('language', 'DE_AT'),
    'DE_BE': ('language', 'DE_BE'),
    'DE_CH': ('language', 'DE_CH'),
    'DE_DE': ('language', 'DE_DE'),
    'DE_LI': ('language', 'DE_LI'),
    'DE_LU': ('language', 'DE_LU'),
    'DeepLTranslator': ('translators.deepl_translator', 'DeepLTranslator'),
    'EL_CY': ('language', 'EL_CY'),
    'EL_GR': ('language', 'EL_GR'),
    'EN_AU': ('language', 'EN_AU'),
    'EN_BW': ('language', 'EN_BW'),
    'EN_CA': ('language', 'EN_CA'),
    'EN_GB': ('language', 'EN_GB'),
    'EN_HK': ('language', 'EN_HK'),
    'EN_IE': ('language', 'EN_IE'),
    'EN_IN': ('language', 'EN_IN'),
    'EN_MT': ('language', 'EN_MT'),
    'EN_NZ': ('language', 'EN_NZ'),
    'EN_PH': ('language', 'EN_PH'),
    'EN_SG': ('language', 'EN_SG'),
    'EN_US': ('language', 'EN_US'),
    'EN_ZW': ('language', 'EN_ZW'),
    'ES_AR': ('language', 'ES_AR'),
    'ES_BO': ('language', 'ES_BO'),
    'ES_CL': ('language', 'ES_CL'),
    'ES_CO': ('language', 'ES_CO'),
    'ES_CR': ('language', 'ES_CR'),
    'ES_DO': ('language', 'ES_DO'),
    'ES_EC': ('language', 'ES_EC'),
    'ES_ES': ('language', 'ES_ES'),
    'ES_GT': ('language', 'ES_GT'),
    'ES_HN': ('language', 'ES_HN'),
    'ES_MX': ('language', 'ES_MX'),
    'ES_NI': ('language', 'ES_NI'),
    'ES_PA': ('language', 'ES_PA'),
    'ES_PE': ('language', 'ES_PE'),
    'ES_PR': ('language', 'ES_PR'),
    'ES_PY': ('language', 'ES_PY'),
    'ES_SV': ('language', 'ES_SV'),
    'ES_US': ('language', 'ES_US'),
    'ES_UY': ('language', 'ES_UY'),
    'ES_VE': ('language', 'ES_VE'),
    'ET_EE': ('language', 'ET_EE'),
    'FI_FI': ('language', 'FI_FI'),
    'FR_BE': ('language', 'FR_BE'),
    'FR_CA': ('language', 'FR_CA'),
    'FR_CH': ('language', 'FR_CH'),
    'FR_FR': ('language', 'FR_FR'),
    'FR_LU': ('language', 'FR_LU'),
    'GU_IN': ('language', 'GU_IN'),
    'HE_IL': ('language', 'HE_IL'),
    'HI_IN': ('language', 'HI_IN'),
    'HR_HR': ('language', 'HR_HR'),
    'HU_HU': ('language', 'HU_HU'),
    'HY_AM': ('language', 'HY_AM'),
    'ID_ID': ('language', 'ID_ID'),
    'IS_IS': ('language', 'IS_IS'),
    'IT_CH': ('language', 'IT_CH'),
    'IT_IT': ('language', 'IT_IT'),
    'JA_JP': ('language', 'JA_JP'),
    'KA_GE': ('language', 'KA_GE'),
    'KK_KZ': ('language', 'KK_KZ'),
    'KN_IN': ('language', 'KN_IN'),
    'KO_KR': ('language', 'KO_KR'),
    'KS_IN': ('language', 'KS_IN'),
    'KU_TR': ('language', 'KU_TR'),
    'KY_KG': ('language', 'KY_KG'),
    'LT_LT': ('language', 'LT_LT'),
    'LV_LV': ('language', 'LV_LV'),
    'Language': ('language', 'Language'),
    'MINIMUM_LANGUAGE_DISTANCE': ('detection', 'MINIMUM_LANGUAGE_DISTANCE'),
    'MK_MK': ('language', 'MK_MK'),
    'ML_IN': ('language', 'ML_IN'),
    'MODEL_NAME': ('translators.marian_translator', 'MODEL_NAME'),
    'MR_IN': ('language', 'MR_IN'),
    'MS_MY': ('language', 'MS_MY'),
    'MT_MT': ('language', 'MT_MT'),
    'MarianTranslator': ('translators.marian_translator', 'MarianTranslator'),
    'NB_NO': ('language', 'NB_NO'),
    'NL_BE': ('language', 'NL_BE'),
    'NL_NL': ('language', 'NL_NL'),
    'NN_NO': ('language', 'NN_NO'),
    'NON_PROSE': ('detection', 'NON_PROSE'),
    'OR_IN': ('language', 'OR_IN'),
    'PA_IN': ('language', 'PA_IN'),
    'PL_PL': ('language', 'PL_PL'),
    'PT_BR': ('language', 'PT_BR'),
    'PT_PT': ('language', 'PT_PT'),
    'RO_RO': ('language', 'RO_RO'),
    'RU_RU': ('language', 'RU_RU'),
    'RU_UA': ('language', 'RU_UA'),
    'SA_IN': ('language', 'SA_IN'),
    'SK_SK': ('language', 'SK_SK'),
    'SL_SI': ('language', 'SL_SI'),
    'SQ_AL': ('language', 'SQ_AL'),
    'SR_ME': ('language', 'SR_ME'),
    'SR_RS': ('language', 'SR_RS'),
    'SV_SE': ('language', 'SV_SE'),
    'TA_IN': ('language', 'TA_IN'),
    'TE_IN': ('language', 'TE_IN'),
    'TH_TH': ('language', 'TH_TH'),
    'TR_TR': ('language', 'TR_TR'),
    'UK_UA': ('language', 'UK_UA'),
    'VI_VN': ('language', 'VI_VN'),
    'ZH_CN': ('language', 'ZH_CN'),
    'ZH_HK': ('language', 'ZH_HK'),
    'ZH_SG': ('language', 'ZH_SG'),
    'ZH_TW': ('language', 'ZH_TW')
}

def __getattr__(name):
    if name in _EXPORTS:
        module, attr = _EXPORTS[name]
        mod = importlib.import_module(f"{__name__}.{module}")
        value = getattr(mod, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'AF_ZA',
    'AITranslator',
    'AR_AE',
    'AR_BH',
    'AR_DZ',
    'AR_EG',
    'AR_IQ',
    'AR_JO',
    'AR_KW',
    'AR_LY',
    'AR_MA',
    'AR_OM',
    'AR_QA',
    'AR_SA',
    'AR_TN',
    'AR_YE',
    'AS_IN',
    'AZ_AZ',
    'ArgosTranslator',
    'BE_BY',
    'BG_BG',
    'BN_IN',
    'BS_BA',
    'C',
    'CA_ES',
    'CS_CZ',
    'DA_DK',
    'DE_AT',
    'DE_BE',
    'DE_CH',
    'DE_DE',
    'DE_LI',
    'DE_LU',
    'DeepLTranslator',
    'EL_CY',
    'EL_GR',
    'EN_AU',
    'EN_BW',
    'EN_CA',
    'EN_GB',
    'EN_HK',
    'EN_IE',
    'EN_IN',
    'EN_MT',
    'EN_NZ',
    'EN_PH',
    'EN_SG',
    'EN_US',
    'EN_ZW',
    'ES_AR',
    'ES_BO',
    'ES_CL',
    'ES_CO',
    'ES_CR',
    'ES_DO',
    'ES_EC',
    'ES_ES',
    'ES_GT',
    'ES_HN',
    'ES_MX',
    'ES_NI',
    'ES_PA',
    'ES_PE',
    'ES_PR',
    'ES_PY',
    'ES_SV',
    'ES_US',
    'ES_UY',
    'ES_VE',
    'ET_EE',
    'FI_FI',
    'FR_BE',
    'FR_CA',
    'FR_CH',
    'FR_FR',
    'FR_LU',
    'GU_IN',
    'HE_IL',
    'HI_IN',
    'HR_HR',
    'HU_HU',
    'HY_AM',
    'ID_ID',
    'IS_IS',
    'IT_CH',
    'IT_IT',
    'JA_JP',
    'KA_GE',
    'KK_KZ',
    'KN_IN',
    'KO_KR',
    'KS_IN',
    'KU_TR',
    'KY_KG',
    'LT_LT',
    'LV_LV',
    'Language',
    'MINIMUM_LANGUAGE_DISTANCE',
    'MK_MK',
    'ML_IN',
    'MODEL_NAME',
    'MR_IN',
    'MS_MY',
    'MT_MT',
    'MarianTranslator',
    'NB_NO',
    'NL_BE',
    'NL_NL',
    'NN_NO',
    'NON_PROSE',
    'OR_IN',
    'PA_IN',
    'PL_PL',
    'PT_BR',
    'PT_PT',
    'RO_RO',
    'RU_RU',
    'RU_UA',
    'SA_IN',
    'SK_SK',
    'SL_SI',
    'SQ_AL',
    'SR_ME',
    'SR_RS',
    'SV_SE',
    'TA_IN',
    'TE_IN',
    'TH_TH',
    'TR_TR',
    'UK_UA',
    'VI_VN',
    'ZH_CN',
    'ZH_HK',
    'ZH_SG',
    'ZH_TW',
    'ai_translator',
    'detection',
    'language',
    'translators'
]
__version__ = '2.0.0'
