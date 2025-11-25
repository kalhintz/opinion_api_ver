# Opinion Trade Auto Trading Bot

Opinion Trade 플랫폼에서 자동으로 YES/NO 주문을 실행하는 Python GUI 봇입니다.

## Features

- 🖥️ Tkinter 기반 GUI 인터페이스
- 📋 일반 토픽(REGULAR) 및 지표 토픽(INDICATOR) 지원
- 💰 다중 토픽 일괄 거래
- 📊 실시간 로그 출력
- ⚙️ 환경변수 기반 설정

## Requirements

- Python 3.8+
- BSC (Binance Smart Chain) 지갑

## Installation
```bash
# 저장소 클론
git clone https://github.com/kalhintz/opinion_api_ver.git
cd opinion_api_ver

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 입력
```

## Configuration

`.env` 파일에 다음 값들을 설정하세요:

| 변수 | 설명 | 필수 |
|------|------|------|
| `PRIVATE_KEY` | BSC 지갑 Private Key | ✅ |
| `SIGNER_ADDRESS` | Signer 지갑 주소 | ✅ |
| `MAKER_ADDRESS` | Maker 지갑 주소 | ✅ |
| `API_KEY` | Opinion Trade API Key | ✅ |
| `RPC_URL` | BSC RPC URL | ❌ |
| `ORDER_AMOUNT` | 기본 주문 금액 (USDT) | ❌ |

## Usage
```bash
python opinion_trade_bot.py
```

### 사용 순서

1. **Client 초기화** - API 연결 설정
2. **토픽 로드** - 거래 가능한 토픽 목록 불러오기
3. **토픽 선택** - 거래할 토픽 선택 (Ctrl+클릭으로 다중 선택)
4. **거래 실행** - 선택한 토픽에 YES/NO 주문 실행

## Screenshot
```
┌─────────────────────────────────────────────────┐
│  Opinion Trade Bot                              │
├─────────────────────────────────────────────────┤
│  [설정]                                         │
│  API Key: xxxxxxxx...                           │
│  Signer: 0x302614...                            │
│  주문 금액: [5.0] USDT                          │
├─────────────────────────────────────────────────┤
│  [Client 초기화] [토픽 로드] [선택한 토픽 거래] │
├──────────────────┬──────────────────────────────┤
│  토픽 목록       │  로그                        │
│  ☐ [R] Topic 1   │  [12:00:01] 초기화 완료      │
│  ☐ [I] Topic 2   │  [12:00:02] 토픽 로드 중...  │
│  ☐ [R] Topic 3   │                              │
└──────────────────┴──────────────────────────────┘
```

## Topic Types

- `[R]` REGULAR - 일반 예측 토픽
- `[I]` INDICATOR - 지표 기반 토픽

## License

MIT License

## Disclaimer

⚠️ **주의**: 이 봇은 실제 자금을 사용합니다. 사용 전 충분히 테스트하고, 손실 가능성을 인지한 상태에서 사용하세요. 투자 결정에 대한 책임은 사용자 본인에게 있습니다.
