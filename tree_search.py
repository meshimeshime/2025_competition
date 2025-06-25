import cv2
import numpy as np

# ─────────────  Author/Work ─────────────

class Author:
    def __init__(self, name, author_id):
        self.name = name
        self.id = author_id

class Work:
    def __init__(self, title, author: Author, work_id: str):
        self.title = title
        self.author = author
        self.id = work_id
        self.references = []

    def add_reference(self, other: "Work"):
        self.references.append(other)

    def generate_reference_paths(self):
        paths = []
        def dfs(node, path):
            path.append(node.id)
            if not node.references:
                path.append(node.author.id)
                paths.append(path.copy())
                path.pop()
            else:
                for child in node.references:
                    dfs(child, path)
            path.pop()
        dfs(self, [])
        return paths

def path_to_string(paths):
    flat = ["->".join(p) for p in paths]
    combined = "|".join(flat)
    bits = "".join(f"{ord(c):08b}" for c in combined)
    return combined  # 사람이 읽을 문자열

# ───────────── 유틸 함수 (한글 지원 버전) ─────────────

def message_to_bits(msg: str) -> str:
    bts = msg.encode("utf-8")
    return "".join(f"{byte:08b}" for byte in bts)

def bits_to_message(bits: str) -> str:
    bytes_list = [
        int(bits[i : i + 8], 2) for i in range(0, len(bits) - len(bits) % 8, 8)
    ]
    try:
        return bytes(bytes_list).decode("utf-8")
    except UnicodeDecodeError as e:
        print("[디코딩 오류 발생] 비트열을 유효한 UTF-8로 해석할 수 없습니다.")
        print(f"원인: {e}")
        print("부분적으로 복원된 바이트열:", bytes(bytes_list))
        raise

# ───────────── 워터마크 삽입/추출 ─────────────

def embed_message(cover_path, out_path, message, block_size=8, alpha=100.0, repeat=5):
    payload = message_to_bits(message)
    L = len(payload)
    header = f"{L:016b}"
    stream = header + payload
    rep = "".join(bit * repeat for bit in stream)

    img = cv2.imread(cover_path)
    ycbcr = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycbcr)
    y = y.astype(np.float32)
    h, w = y.shape

    coords = [
        (yy, xx)
        for yy in range(0, h - block_size + 1, block_size)
        for xx in range(0, w - block_size + 1, block_size)
    ]

    if len(rep) > len(coords):
        raise ValueError(f"워터마크 데이터가 너무 커서 삽입할 수 없습니다. "
                         f"(요구 블록 수: {len(rep)}, 사용 가능: {len(coords)})")

    coords = coords[:len(rep)]

    for i, bit in enumerate(rep):
        yy, xx = coords[i]
        block = y[yy : yy + block_size, xx : xx + block_size]
        d = cv2.dct(block)
        d[4, 3] = abs(d[4, 3]) + alpha if bit == "1" else -abs(d[4, 3]) - alpha
        y[yy : yy + block_size, xx : xx + block_size] = cv2.idct(d)

    y = np.clip(y, 0, 255).astype(np.uint8)
    wm = cv2.merge([y, cr, cb])
    out_img = cv2.cvtColor(wm, cv2.COLOR_YCrCb2BGR)
    if not out_path.lower().endswith(".png"):
        out_path += ".png"
    cv2.imwrite(out_path, out_img)
    print(f"'{out_path}'에 메시지 워터마킹 완료! ({L} bits)")

def extract_message(image_path, block_size=8, repeat=5) -> str:
    img = cv2.imread(image_path)
    y = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)[:, :, 0].astype(np.float32)
    h, w = y.shape

    coords = [
        (yy, xx)
        for yy in range(0, h - block_size + 1, block_size)
        for xx in range(0, w - block_size + 1, block_size)
    ]

    raw_hdr = [
        '1' if cv2.dct(y[yy:yy+block_size, xx:xx+block_size])[4,3] > 0 else '0'
        for yy, xx in coords[:16*repeat]
    ]
    header = ''.join(
        '1' if raw_hdr[j*repeat:(j+1)*repeat].count('1') > repeat//2 else '0'
        for j in range(16)
    )
    L = int(header, 2)
    if L == 0:
        print("⚠️ 복원할 메시지 길이 0입니다.")
        return ""

    total = (16 + L) * repeat
    raw = [
        '1' if cv2.dct(y[yy:yy+block_size, xx:xx+block_size])[4,3] > 0 else '0'
        for yy, xx in coords[:total]
    ]
    bits = ''.join(
        '1' if raw[k*repeat:(k+1)*repeat].count('1') > repeat//2 else '0'
        for k in range(16 + L)
    )[16:]

    print("🚩 추출된 헤더 비트:", header)
    print("🚩 해석된 길이 L:", L)
    print("🚩 총 필요한 블록 수:", (16+L)*repeat)
    print("🚩 전체 좌표 수:", len(coords))

    try:
        return bits_to_message(bits)
    except UnicodeDecodeError as e:
        print("[❌ UTF-8 디코딩 실패] 복원된 비트열:", bits[:64], "...")
        raise

# ───────────── 메인 (콘솔 테스트용) ─────────────

if __name__ == "__main__":
    n_auth = int(input(" 작가 수: "))
    authors = {}
    for _ in range(n_auth):
        name = input("  - 작가 이름: ")
        aid = input("  - 작가 ID: ")
        authors[aid] = Author(name, aid)

    n_work = int(input(" 작품 수: "))
    works = {}
    for _ in range(n_work):
        wid = input("  - 작품 ID (예: W001): ")
        title = input("  - 작품 제목: ")
        aid = input("  - 이 작품의 작가 ID: ")
        works[wid] = Work(title, authors[aid], wid)

    print("▶ 참조 관계를 입력하세요 (빈칸 입력 시 종료)")
    while True:
        src = input("  - 참조하는 작품 ID (parent): ")
        if not src:
            break
        dst = input("  - 참조되는 작품 ID (child): ")
        works[src].add_reference(works[dst])

    root_id = input(" 워터마크 찍을 루트 작품 ID: ")
    root = works[root_id]

    paths = root.generate_reference_paths()
    msg = path_to_string(paths)
    print("\n 생성된 참조 경로 문자열:")
    print(msg)

    cover = input("\n 원본 이미지 파일: ")
    out = input(" 워터마크 이미지 이름: ")
    embed_message(cover, out, msg)

    wmfile = input("\n 검출할 워터마크 이미지: ")
    restored = extract_message(wmfile)
    print("\n 복원된 문자열:")
    print(restored)
