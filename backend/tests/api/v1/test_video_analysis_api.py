import pytest
import httpx
from pathlib import Path
from io import BytesIO
import cv2
import numpy as np

from backend.main import app
from backend.core.database import get_db
from backend.models.user import User
from backend.models.project import Project
from backend.models.data_source import DataSource
from backend.core.config import settings

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_test_video_bytes() -> tuple[str, BytesIO]:
    """创建测试视频文件的字节流"""
    # 创建临时视频文件
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 30.0
    width, height = 320, 240
    
    # 使用临时文件创建视频
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        out = cv2.VideoWriter(tmp_file.name, fourcc, fps, (width, height))
        
        # 生成15帧视频（0.5秒）
        for i in range(15):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [i * 16, 100, 200 - i * 12]  # 渐变颜色
            out.write(frame)
        
        out.release()
        
        # 读取文件内容到BytesIO
        with open(tmp_file.name, 'rb') as f:
            video_bytes = BytesIO(f.read())
        
        # 清理临时文件
        Path(tmp_file.name).unlink()
        
        return ("test_video.mp4", video_bytes)


class TestVideoAnalysisAPI:
    """视频分析API测试类"""
    
    async def test_upload_video_file(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试视频文件上传"""
        # 设置上传目录
        monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
        
        # 创建测试视频
        video_name, video_bytes = create_test_video_bytes()
        
        # 上传视频文件
        upload_url = f"/api/v1/data_sources/upload?project_id={test_project.id}"
        response = await async_client.post(
            upload_url,
            files={"file": (video_name, video_bytes, "video/mp4")},
            headers=auth_headers
        )
        
        # 验证上传响应
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == video_name
        assert data["file_type"] == "mp4"
        assert data["analysis_category"] == "VIDEO"
        
        return data["id"]
    
    async def test_get_video_analysis_status(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试获取视频分析状态"""
        # 先上传视频文件
        data_source_id = await self.test_upload_video_file(
            async_client, auth_headers, test_project, tmp_path, monkeypatch
        )
        
        # 获取数据源详情（包含分析状态）
        detail_url = f"/api/v1/data_sources/{data_source_id}?project_id={test_project.id}"
        response = await async_client.get(detail_url, headers=auth_headers)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == data_source_id
        assert "profile_status" in data
        assert data["profile_status"] in ["pending", "in_progress", "completed", "failed"]
    
    async def test_trigger_video_analysis(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试触发视频分析"""
        # 先上传视频文件
        data_source_id = await self.test_upload_video_file(
            async_client, auth_headers, test_project, tmp_path, monkeypatch
        )
        
        # 触发分析
        analyze_url = f"/api/v1/data_sources/{data_source_id}/analyze?project_id={test_project.id}"
        response = await async_client.post(analyze_url, headers=auth_headers)
        
        # 验证响应
        assert response.status_code in [200, 202]  # 200: 同步完成, 202: 异步处理
        data = response.json()
        
        if response.status_code == 202:
            # 异步处理情况
            assert "task_id" in data
            assert "message" in data
        else:
            # 同步完成情况
            assert "status" in data
            assert data["status"] in ["success", "completed"]
    
    async def test_get_video_analysis_report(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试获取视频分析报告"""
        # 先上传视频文件
        data_source_id = await self.test_upload_video_file(
            async_client, auth_headers, test_project, tmp_path, monkeypatch
        )
        
        # 等待分析完成（在测试环境中应该是同步的）
        # 这里可能需要轮询状态直到完成
        
        # 获取分析报告
        report_url = f"/api/v1/data_sources/{data_source_id}?project_id={test_project.id}"
        response = await async_client.get(report_url, headers=auth_headers)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        # 检查是否有分析结果
        if data.get("profile_status") == "completed" and data.get("profiling_result"):
            result = data["profiling_result"]
            assert result["analysis_type"] in ["video", "video_enhanced"]
            
            # 验证视频分析结果的基本结构
            if result["analysis_type"] == "video_enhanced":
                assert "enhanced_metadata" in result
                assert "width" in result["enhanced_metadata"]
                assert "height" in result["enhanced_metadata"]
            else:
                assert "video_properties" in result
                assert "width" in result["video_properties"]
                assert "height" in result["video_properties"]
    
    async def test_video_analysis_error_handling(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project
    ):
        """测试视频分析错误处理"""
        # 测试不存在的数据源ID
        fake_id = 99999
        analyze_url = f"/api/v1/data_sources/{fake_id}/analyze?project_id={test_project.id}"
        response = await async_client.post(analyze_url, headers=auth_headers)
        
        # 验证错误响应
        assert response.status_code == 404
        
        # 测试无效的项目ID
        detail_url = f"/api/v1/data_sources/1?project_id=99999"
        response = await async_client.get(detail_url, headers=auth_headers)
        
        # 验证错误响应
        assert response.status_code in [403, 404]  # 权限错误或不存在
    
    async def test_video_analysis_permissions(
        self,
        async_client: httpx.AsyncClient,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试视频分析权限控制"""
        # 测试未认证访问
        data_source_id = 1
        analyze_url = f"/api/v1/data_sources/{data_source_id}/analyze?project_id={test_project.id}"
        response = await async_client.post(analyze_url)  # 不提供认证头
        
        # 验证需要认证
        assert response.status_code == 401
        
        # 测试无效token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.post(analyze_url, headers=invalid_headers)
        
        # 验证token无效
        assert response.status_code == 401


class TestVideoAnalysisIntegrationAPI:
    """视频分析集成API测试类"""
    
    async def test_full_video_analysis_workflow(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试完整的视频分析工作流"""
        # 设置上传目录
        monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
        
        # 1. 上传视频文件
        video_name, video_bytes = create_test_video_bytes()
        upload_url = f"/api/v1/data_sources/upload?project_id={test_project.id}"
        upload_response = await async_client.post(
            upload_url,
            files={"file": (video_name, video_bytes, "video/mp4")},
            headers=auth_headers
        )
        
        assert upload_response.status_code == 201
        data_source_id = upload_response.json()["id"]
        
        # 2. 检查初始状态
        detail_url = f"/api/v1/data_sources/{data_source_id}?project_id={test_project.id}"
        status_response = await async_client.get(detail_url, headers=auth_headers)
        
        assert status_response.status_code == 200
        initial_data = status_response.json()
        assert initial_data["profile_status"] in ["pending", "in_progress", "completed"]
        
        # 3. 如果需要，触发分析
        if initial_data["profile_status"] == "pending":
            analyze_url = f"/api/v1/data_sources/{data_source_id}/analyze?project_id={test_project.id}"
            analyze_response = await async_client.post(analyze_url, headers=auth_headers)
            assert analyze_response.status_code in [200, 202]
        
        # 4. 获取最终结果
        final_response = await async_client.get(detail_url, headers=auth_headers)
        assert final_response.status_code == 200
        final_data = final_response.json()
        
        # 5. 验证分析结果
        if final_data.get("profile_status") == "completed":
            assert "profiling_result" in final_data
            result = final_data["profiling_result"]
            assert result["analysis_type"] in ["video", "video_enhanced"]
            
            # 验证基本视频信息
            if "enhanced_metadata" in result:
                metadata = result["enhanced_metadata"]
                assert metadata["width"] > 0
                assert metadata["height"] > 0
                assert metadata["fps"] > 0
            elif "video_properties" in result:
                props = result["video_properties"]
                assert props["width"] > 0
                assert props["height"] > 0
    
    async def test_video_analysis_performance_api(
        self,
        async_client: httpx.AsyncClient,
        auth_headers: dict,
        test_project: Project,
        tmp_path: Path,
        monkeypatch
    ):
        """测试视频分析API性能"""
        import time
        
        # 设置上传目录
        monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行完整工作流
        await self.test_full_video_analysis_workflow(
            async_client, auth_headers, test_project, tmp_path, monkeypatch
        )
        
        # 计算总时间
        total_time = time.time() - start_time
        
        # 验证性能要求（小视频文件应在30秒内完成整个流程）
        assert total_time < 30, f"视频分析API工作流耗时过长: {total_time:.2f}秒"


# 运行测试的辅助函数
def test_video_api_basic():
    """基础API测试函数"""
    print("🧪 测试视频分析API基础功能...")
    
    # 测试视频文件创建
    try:
        video_name, video_bytes = create_test_video_bytes()
        assert video_name == "test_video.mp4"
        assert len(video_bytes.getvalue()) > 0
        print("✅ 测试视频文件创建成功")
    except Exception as e:
        print(f"❌ 测试视频文件创建失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # 直接运行时的测试入口
    print("🎬 视频分析API测试套件")
    print("=" * 50)
    
    # 运行基础测试
    if test_video_api_basic():
        print("\n🎉 基础API测试通过！")
        print("💡 提示: 使用 'pytest backend/tests/api/v1/test_video_analysis_api.py' 运行完整API测试套件")
    else:
        print("\n❌ 基础API测试失败！") 