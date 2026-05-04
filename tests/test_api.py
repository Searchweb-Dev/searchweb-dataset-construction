"""API 통합 테스트."""

from fastapi.testclient import TestClient


def test_create_folder(client: TestClient):
    """폴더 생성."""
    response = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Tech Bookmarks"}
    )
    assert response.status_code == 201
    folder_id = response.json()["member_folder_id"]
    assert folder_id > 0


def test_save_link(client: TestClient):
    """링크 저장."""
    # 폴더 생성
    folder_resp = client.post(
        "/api/v1/members/1/folders",
        json={"folder_name": "Links"}
    )
    folder_id = folder_resp.json()["member_folder_id"]
    
    # 링크 저장
    response = client.post(
        "/api/v1/members/1/saved_links",
        json={
            "url": "https://example.com",
            "display_title": "Example Article",
            "folder_id": folder_id,
        }
    )
    assert response.status_code == 201
    assert response.json()["display_title"] == "Example Article"


def test_url_normalization(client: TestClient):
    """URL 정규화 (쿼리 파라미터 정렬)."""
    folder_resp = client.post(
        "/api/v1/members/2/folders",
        json={"folder_name": "Folder"}
    )
    folder_id = folder_resp.json()["member_folder_id"]
    
    # 첫 저장 (쿼리 파라미터 순서 1)
    resp1 = client.post(
        "/api/v1/members/2/saved_links",
        json={
            "url": "https://example.org?a=1&b=2",
            "display_title": "Link1",
            "folder_id": folder_id,
        }
    )
    link_id_1 = resp1.json()["link_id"]
    
    # 두 번째 저장 (쿼리 파라미터 순서 2 - 정규화 후 같음)
    resp2 = client.post(
        "/api/v1/members/2/saved_links",
        json={
            "url": "https://example.org?b=2&a=1",
            "display_title": "Link2",
            "folder_id": folder_id,
        }
    )
    link_id_2 = resp2.json()["link_id"]
    
    # 정규화 후 동일 링크여야 함
    assert link_id_1 == link_id_2


def test_create_tag(client: TestClient):
    """태그 생성."""
    import time
    tag_name = f"python-{int(time.time() * 1000)}"
    response = client.post(
        "/api/v1/members/3/tags",
        json={"tag_name": tag_name}
    )
    assert response.status_code == 201
    assert response.json()["tag_name"] == tag_name


def test_attach_tag(client: TestClient):
    """링크에 태그 부착."""
    import time
    tag_name = f"tag-{int(time.time() * 1000)}"
    # 폴더, 링크, 태그 생성
    folder = client.post("/api/v1/members/4/folders", json={"folder_name": "F"}).json()
    link = client.post(
        "/api/v1/members/4/saved_links",
        json={"url": "https://test.com", "display_title": "T", "folder_id": folder["member_folder_id"]}
    ).json()
    tag = client.post("/api/v1/members/4/tags", json={"tag_name": tag_name}).json()
    
    # 태그 부착
    response = client.post(
        f"/api/v1/members/4/saved_links/{link['member_saved_link_id']}/tags",
        json={"tag_id": tag["member_tag_id"]}
    )
    assert response.status_code == 201


def test_get_link(client: TestClient):
    """링크 조회."""
    # 링크 생성
    folder = client.post("/api/v1/members/5/folders", json={"folder_name": "F"}).json()
    link = client.post(
        "/api/v1/members/5/saved_links",
        json={"url": "https://article.io", "display_title": "Article", "folder_id": folder["member_folder_id"]}
    ).json()
    
    # 조회
    response = client.get(f"/api/v1/links/{link['link_id']}")
    assert response.status_code == 200
    assert response.json()["link_id"] == link["link_id"]
