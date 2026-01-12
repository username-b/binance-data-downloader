from abc import ABC, abstractmethod
import pandas as pd


class FeatureBuilder(ABC):
    """
    Базовый контракт любого билдера фичей.
    """

    source: str          # имя источника (klines, aggTrades, ...)
    needs_reference: bool = False

    @abstractmethod
    def build(
        self,
        df_raw: pd.DataFrame,
        df_ref: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        pass
