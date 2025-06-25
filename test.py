import os
import uuid
from tree_search import (
    embed_message,
    extract_message,
)  # 너의 코드가 저장된 파일명에 맞게 수정


def test_watermark_embedding_and_extraction():
    cover_img_path = "test_images/starry_night.png"  # 테스트용 원본 이미지 (존재해야 함)
    temp_output_img = f"test_images/output_{uuid.uuid4().hex}.png"
    message = "작품ID->다른작품ID->작가ID"

    print("1. 메시지 워터마크 삽입 중...")
    embed_message(cover_img_path, temp_output_img, message)

    print("2. 워터마크 검출 중...")
    decoded = extract_message(temp_output_img)

    print(f"\n[삽입된 메시지] {message}")
    print(f"[복원된 메시지] {decoded}")

    assert (
        message == decoded
    ), "❌ 워터마크 복원 실패! 삽입된 메시지와 복원된 메시지가 다릅니다."
    print("\n✅ 테스트 통과: 메시지가 정확히 삽입되고 복원되었습니다.")

    # 정리
    if os.path.exists(temp_output_img):
        os.remove(temp_output_img)


if __name__ == "__main__":
    test_watermark_embedding_and_extraction()
