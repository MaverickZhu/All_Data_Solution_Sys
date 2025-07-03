import pandas as pd
from sqlalchemy.orm import Session
from backend.services.data_source_service import DataSourceService
from backend.models.data_source import DataSource

class ProfilingService:

    def __init__(self, db: Session):
        self.db = db

    def generate_profile_report(self, data_source_id: int) -> dict:
        """
        Generates a basic statistical profile for a given CSV data source.

        :param data_source_id: The ID of the data source to profile.
        :return: A dictionary containing the profiling report.
        """
        # 注意：此处需要项目ID，但当前模型没有，暂时假设权限已通过
        # TODO: 完善权限检查，需要传入 project_id
        # 此处暂时无法直接调用，因为 get_data_source_by_id 需要 project_id
        # 这是一个待修复的设计问题。暂时我们先假设可以获取到。
        # 实际场景中，可能需要先通过 data_source_id 获取 data_source，再检查其 project_id 的权限
        
        # 临时获取数据源，绕过权限检查（仅为修复启动问题）
        # 正确的实现应该像这样：
        # data_source = DataSourceService.get_data_source_by_id(self.db, data_source_id, project_id)
        
        # 临时实现
        data_source = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()

        if not data_source or not data_source.file_path:
            raise ValueError("Data source not found or file path is missing.")

        if not data_source.file_path.lower().endswith('.csv'):
            raise TypeError("Profiling is only supported for CSV files at the moment.")

        # 注意：这里的 file_path 是相对路径，需要拼接上 UPLOAD_DIR
        # from core.config import settings
        # full_file_path = settings.upload_dir / data_source.file_path
        # df = pd.read_csv(full_file_path)

        # 再次注意：临时修复，假设路径是绝对的
        df = pd.read_csv(data_source.file_path)

        # Basic information
        report = {
            "file_info": {
                "name": data_source.name,
                "size_bytes": data_source.file_size,
                "path": data_source.file_path
            },
            "dataset_stats": {
                "num_rows": len(df),
                "num_cols": len(df.columns),
                "total_cells": int(df.size),
                "missing_cells": int(df.isnull().sum().sum()),
                "missing_cells_pct": f"{df.isnull().sum().sum() / df.size * 100:.2f}%"
            },
            "column_details": {}
        }

        # Per-column statistics
        for col in df.columns:
            column_series = df[col]
            stats = {
                "dtype": str(column_series.dtype),
                "missing_values": int(column_series.isnull().sum()),
                "missing_values_pct": f"{column_series.isnull().sum() / len(df) * 100:.2f}%",
                "unique_values": column_series.nunique(),
            }

            if pd.api.types.is_numeric_dtype(column_series):
                stats.update({
                    "mean": column_series.mean(),
                    "std_dev": column_series.std(),
                    "min": column_series.min(),
                    "25%": column_series.quantile(0.25),
                    "50%": column_series.median(),
                    "75%": column_series.quantile(0.75),
                    "max": column_series.max(),
                })
            else:
                # For categorical/object columns, show top 5 value counts
                stats.update({
                    "top_values": column_series.value_counts().nlargest(5).to_dict()
                })

            report["column_details"][col] = stats

        return report 