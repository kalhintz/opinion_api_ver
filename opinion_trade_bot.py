#!/usr/bin/env python3
"""
Opinion Trade 자동 거래 봇 (Python GUI 버전)
"""

import os
import threading
import time
import requests
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox
from dotenv import load_dotenv
from opinion_clob_sdk import Client
from opinion_clob_sdk.chain.py_order_utils.model.order import PlaceOrderDataInput
from opinion_clob_sdk.chain.py_order_utils.model.sides import OrderSide
from opinion_clob_sdk.chain.py_order_utils.model.order_type import LIMIT_ORDER

# 환경변수 로드
load_dotenv()

class OpinionTradeBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Opinion Trade Bot")
        self.root.geometry("1000x700")

        # 설정
        self.api_key = os.getenv('API_KEY', '')
        self.rpc_url = os.getenv('RPC_URL', 'https://bsc-dataseed.binance.org')
        self.private_key = os.getenv('PRIVATE_KEY', '')
        self.signer_address = os.getenv('SIGNER_ADDRESS', '')
        self.maker_address = os.getenv('MAKER_ADDRESS', '')
        self.order_amount = float(os.getenv('ORDER_AMOUNT', '5.0'))

        self.client = None
        self.topics = []
        self.selected_topics = []

        self.create_widgets()

    def create_widgets(self):
        # 상단 설정 패널
        config_frame = ttk.LabelFrame(self.root, text="설정", padding=10)
        config_frame.pack(fill=X, padx=10, pady=5)

        # API Key
        ttk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.api_key_var = StringVar(value=self.api_key[:20] + "...")
        ttk.Entry(config_frame, textvariable=self.api_key_var, width=40, state='readonly').grid(row=0, column=1, padx=5, pady=2)

        # Signer
        ttk.Label(config_frame, text="Signer:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.signer_var = StringVar(value=self.signer_address)
        ttk.Entry(config_frame, textvariable=self.signer_var, width=50, state='readonly').grid(row=1, column=1, padx=5, pady=2)

        # Maker
        ttk.Label(config_frame, text="Maker:").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.maker_var = StringVar(value=self.maker_address)
        ttk.Entry(config_frame, textvariable=self.maker_var, width=50, state='readonly').grid(row=2, column=1, padx=5, pady=2)

        # 주문 금액
        ttk.Label(config_frame, text="주문 금액:").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        self.amount_var = DoubleVar(value=self.order_amount)
        amount_entry = ttk.Entry(config_frame, textvariable=self.amount_var, width=20)
        amount_entry.grid(row=3, column=1, sticky=W, padx=5, pady=2)
        ttk.Label(config_frame, text="USDT").grid(row=3, column=2, sticky=W, padx=5, pady=2)

        # 토픽 개수
        ttk.Label(config_frame, text="로드할 토픽 개수:").grid(row=4, column=0, sticky=W, padx=5, pady=2)
        self.limit_var = IntVar(value=50)
        limit_entry = ttk.Entry(config_frame, textvariable=self.limit_var, width=20)
        limit_entry.grid(row=4, column=1, sticky=W, padx=5, pady=2)
        ttk.Label(config_frame, text="개 (페이지당 로드)").grid(row=4, column=2, sticky=W, padx=5, pady=2)

        # 토픽 타입 필터
        ttk.Label(config_frame, text="토픽 타입:").grid(row=5, column=0, sticky=W, padx=5, pady=2)
        self.topic_type_var = StringVar(value="ALL")
        type_combo = ttk.Combobox(config_frame, textvariable=self.topic_type_var, width=18, state='readonly')
        type_combo['values'] = ('ALL', 'REGULAR', 'INDICATOR')
        type_combo.grid(row=5, column=1, sticky=W, padx=5, pady=2)
        ttk.Label(config_frame, text="(REGULAR=일반, INDICATOR=지표)").grid(row=5, column=2, sticky=W, padx=5, pady=2)

        # 버튼 프레임
        button_frame = Frame(self.root)
        button_frame.pack(fill=X, padx=10, pady=5)

        self.init_btn = ttk.Button(button_frame, text="Client 초기화", command=self.init_client)
        self.init_btn.pack(side=LEFT, padx=5)

        self.load_btn = ttk.Button(button_frame, text="토픽 로드", command=self.load_topics, state=DISABLED)
        self.load_btn.pack(side=LEFT, padx=5)

        self.trade_btn = ttk.Button(button_frame, text="선택한 토픽 거래", command=self.execute_trading, state=DISABLED)
        self.trade_btn.pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="로그 지우기", command=self.clear_log).pack(side=RIGHT, padx=5)

        # 중간 패널 - 토픽 리스트와 로그
        main_frame = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # 왼쪽 - 토픽 리스트
        topic_frame = ttk.LabelFrame(main_frame, text="토픽 목록", padding=10)
        main_frame.add(topic_frame, weight=1)

        # 토픽 리스트박스 (스크롤바 포함)
        topic_scroll_frame = Frame(topic_frame)
        topic_scroll_frame.pack(fill=BOTH, expand=True)

        topic_scrollbar = Scrollbar(topic_scroll_frame)
        topic_scrollbar.pack(side=RIGHT, fill=Y)

        self.topic_listbox = Listbox(topic_scroll_frame, selectmode=MULTIPLE, yscrollcommand=topic_scrollbar.set)
        self.topic_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        topic_scrollbar.config(command=self.topic_listbox.yview)

        ttk.Button(topic_frame, text="전체 선택", command=self.select_all_topics).pack(fill=X, pady=5)

        # 오른쪽 - 로그
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding=10)
        main_frame.add(log_frame, weight=2)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=WORD, width=60, height=30)
        self.log_text.pack(fill=BOTH, expand=True)

        # 상태바
        self.status_var = StringVar(value="대기 중...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.pack(fill=X, side=BOTTOM, padx=10, pady=5)

    def log(self, message, level="INFO"):
        """로그 출력"""
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "INFO": "black",
            "SUCCESS": "green",
            "ERROR": "red",
            "WARNING": "orange"
        }

        self.log_text.insert(END, f"[{timestamp}] {message}\n")

        # 마지막 줄 색상 변경
        line_start = self.log_text.index("end-2c linestart")
        line_end = self.log_text.index("end-1c")
        self.log_text.tag_add(level, line_start, line_end)
        self.log_text.tag_config(level, foreground=colors.get(level, "black"))

        self.log_text.see(END)
        self.root.update()

    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, END)

    def update_status(self, message):
        """상태바 업데이트"""
        self.status_var.set(message)
        self.root.update()

    def init_client(self):
        """Client 초기화"""
        try:
            self.update_status("Client 초기화 중...")
            self.log("=" * 60, "INFO")
            self.log("Opinion Trade Client 초기화", "INFO")
            self.log("=" * 60, "INFO")

            if not self.private_key:
                messagebox.showerror("오류", "PRIVATE_KEY가 설정되지 않았습니다.\n.env 파일을 확인하세요.")
                return

            self.order_amount = self.amount_var.get()

            self.log(f"API Key: {self.api_key[:8]}...", "INFO")
            self.log(f"Signer: {self.signer_address}", "INFO")
            self.log(f"Maker: {self.maker_address}", "INFO")
            self.log(f"주문 금액: {self.order_amount} USDT", "INFO")

            self.client = Client(
                host='https://proxy.opinion.trade:8443',
                apikey=self.api_key,
                chain_id=56,
                rpc_url=self.rpc_url,
                private_key=self.private_key,
                multi_sig_addr=self.maker_address,
                conditional_tokens_addr='0xAD1a38cEc043e70E83a3eC30443dB285ED10D774',
                multisend_addr='0x998739BFdAAdde7C933B942a68053933098f9EDa'
            )

            self.log("✅ Client 초기화 완료", "SUCCESS")
            self.update_status("Client 초기화 완료")

            self.init_btn.config(state=DISABLED)
            self.load_btn.config(state=NORMAL)

        except Exception as e:
            self.log(f"❌ Client 초기화 실패: {e}", "ERROR")
            self.update_status("초기화 실패")
            messagebox.showerror("초기화 실패", str(e))

    def load_topics(self):
        """토픽 로드 (일반 + 지표 토픽)"""
        def load():
            try:
                target_limit = self.limit_var.get()
                if target_limit < 1:
                    messagebox.showwarning("경고", "토픽 개수는 1개 이상으로 설정하세요.")
                    return

                topic_type_filter = self.topic_type_var.get()

                self.update_status("토픽 로딩 중...")
                self.log(f"🔎 토픽 로딩 시작 (목표: {target_limit}개, 타입: {topic_type_filter})", "INFO")

                all_topics = []

                # 1. 일반 토픽 로드 (/api/v2/topic)
                if topic_type_filter in ['ALL', 'REGULAR']:
                    self.log("📋 일반 토픽 로딩 중...", "INFO")
                    regular_topics = self.load_regular_topics(target_limit)
                    for topic in regular_topics:
                        topic['_type'] = 'REGULAR'
                    all_topics.extend(regular_topics)
                    self.log(f"   ✅ 일반 토픽: {len(regular_topics)}개", "SUCCESS")

                # 2. 지표 토픽 로드 (/api/v2/indicator)
                if topic_type_filter in ['ALL', 'INDICATOR']:
                    self.log("📊 지표 토픽 로딩 중...", "INFO")
                    indicator_topics = self.load_indicator_topics(target_limit)
                    for topic in indicator_topics:
                        topic['_type'] = 'INDICATOR'
                    all_topics.extend(indicator_topics)
                    self.log(f"   ✅ 지표 토픽: {len(indicator_topics)}개", "SUCCESS")

                # 목표 개수만큼만 저장
                self.topics = all_topics[:target_limit]
                self.log(f"✅ 총 {len(self.topics)}개 토픽 로드 완료", "SUCCESS")

                # 리스트박스에 추가
                self.topic_listbox.delete(0, END)
                for idx, topic in enumerate(self.topics):
                    # 토픽 타입 표시
                    topic_type = topic.get('_type', 'UNKNOWN')
                    type_label = f"[{topic_type[0]}]"  # [R] 또는 [I]

                    # 제목 추출
                    title = topic.get('title', 'Unknown')
                    topic_id = topic.get('topicId', 'N/A')

                    if not title or title == 'Unknown':
                        title = "No Title"

                    # 제목 길이 제한
                    if len(title) > 65:
                        title = title[:65] + "..."

                    display_text = f"{type_label} [{topic_id}] {title}"
                    self.topic_listbox.insert(END, display_text)

                self.update_status(f"{len(self.topics)}개 토픽 로드 완료")
                self.trade_btn.config(state=NORMAL)

            except Exception as e:
                self.log(f"❌ 토픽 로딩 실패: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "ERROR")
                self.update_status("토픽 로딩 실패")
                messagebox.showerror("로딩 실패", str(e))

        threading.Thread(target=load, daemon=True).start()

    def load_regular_topics(self, limit):
        """일반 토픽 로드 (/api/v2/topic)"""
        all_topics = []
        page = 1
        per_page = 20

        while len(all_topics) < limit:
            url = "https://proxy.opinion.trade:8443/api/bsc/api/v2/topic"
            params = {
                "page": page,
                "limit": per_page,
                "sortBy": "1",
                "chainId": "56",
                "status": "2",  # ACTIVATED
                "isShow": "1",
                "topicType": "2",
                "indicatorType": "2"
            }

            headers = {
                "accept": "application/json",
                "apikey": self.api_key
            }

            response = requests.get(url, params=params, headers=headers)

            if response.status_code != 200:
                break

            data = response.json()

            if data.get('errno') != 0:
                break

            result = data.get('result', {})
            topics_in_page = result.get('list', [])

            if not topics_in_page:
                break

            all_topics.extend(topics_in_page)

            if len(topics_in_page) < per_page:
                break

            page += 1
            time.sleep(0.2)

        return all_topics[:limit]

    def load_indicator_topics(self, limit):
        """지표 토픽 로드 (/api/v2/indicator)"""
        all_topics = []
        page = 1
        per_page = 20

        while len(all_topics) < limit:
            url = "https://proxy.opinion.trade:8443/api/bsc/api/v2/indicator"
            params = {
                "page": page,
                "limit": per_page,
                "chainId": "56"
            }

            headers = {
                "accept": "application/json",
                "apikey": self.api_key
            }

            response = requests.get(url, params=params, headers=headers)

            if response.status_code != 200:
                break

            data = response.json()

            if data.get('errno') != 0:
                break

            result = data.get('result', {})
            indicators = result.get('list', [])

            if not indicators:
                break

            # indicator를 토픽 형식으로 변환
            for indicator in indicators:
                topic_data = indicator.get('topic', {})
                if topic_data:
                    # indicator 제목 사용
                    topic_data['title'] = indicator.get('title', topic_data.get('title', ''))
                    topic_data['indicatorId'] = indicator.get('id')
                    all_topics.append(topic_data)

            if len(indicators) < per_page:
                break

            page += 1
            time.sleep(0.2)

        return all_topics[:limit]

    def select_all_topics(self):
        """전체 토픽 선택"""
        self.topic_listbox.select_set(0, END)

    def execute_trading(self):
        """거래 실행 (JavaScript 방식과 동일)"""
        selected_indices = self.topic_listbox.curselection()

        if not selected_indices:
            messagebox.showwarning("경고", "거래할 토픽을 선택하세요.")
            return

        selected_topics = [self.topics[i] for i in selected_indices]

        # ✅ 최신 Order Amount 값 읽기
        current_order_amount = self.amount_var.get()

        confirm = messagebox.askyesno(
            "거래 확인",
            f"{len(selected_topics)}개 토픽에 거래를 시작하시겠습니까?\n\n"
            f"주문 금액: {current_order_amount} USDT per order"
        )

        if not confirm:
            return

        def trade():
            try:
                self.update_status("거래 실행 중...")
                self.trade_btn.config(state=DISABLED)
                self.load_btn.config(state=DISABLED)

                total_success = 0
                total_fail = 0

                for topic_idx, topic in enumerate(selected_topics, 1):
                    # 딕셔너리로 접근 (JavaScript와 동일)
                    topic_id = topic.get('topicId')
                    title = topic.get('title', 'Unknown')
                    child_list = topic.get('childList', [])

                    # childList가 없으면 topic 자체를 사용
                    if not child_list:
                        child_list = [topic]

                    if not topic_id:
                        self.log(f"❌ Topic ID 없음: {title}", "ERROR")
                        total_fail += len(child_list) * 2
                        continue

                    self.log("\n" + "=" * 60, "INFO")
                    self.log(f"💰 거래 시작 [{topic_idx}/{len(selected_topics)}]", "INFO")
                    self.log(f"   제목: {title}", "INFO")
                    self.log(f"   Topic ID: {topic_id}", "INFO")
                    self.log(f"   {len(child_list)}개 옵션 × 2 (YES/NO) = {len(child_list) * 2}개 주문", "INFO")
                    self.log(f"   주문 금액: {current_order_amount} USDT", "INFO")
                    self.log("=" * 60, "INFO")

                    try:
                        for child_idx, child in enumerate(child_list, 1):
                            child_topic_id = child.get('topicId')
                            child_title = child.get('title', '')
                            yes_pos = child.get('yesPos', '')
                            no_pos = child.get('noPos', '')
                            yes_price = child.get('yesBuyPrice', '0.5')
                            no_price = child.get('noBuyPrice', '0.5')

                            self.log(f"\n[{child_idx}/{len(child_list)}] {child_title} (topicId={child_topic_id})", "INFO")

                            # YES 주문
                            if yes_pos:
                                self.log(f"  → YES 주문 ({current_order_amount} USDT, price={yes_price})...", "INFO")
                                success, result = self.place_order(child_topic_id, yes_pos, OrderSide.BUY, yes_price, current_order_amount)

                                if success:
                                    self.log(f"     ✅ YES 성공 (Order ID: {result})", "SUCCESS")
                                    total_success += 1
                                else:
                                    self.log(f"     ❌ YES 실패: {result}", "ERROR")
                                    total_fail += 1

                                time.sleep(0.5)
                            else:
                                self.log("  ⚠️  YES: yesPos 없음, 스킵", "WARNING")
                                total_fail += 1

                            # NO 주문
                            if no_pos:
                                self.log(f"  → NO 주문 ({current_order_amount} USDT, price={no_price})...", "INFO")
                                success, result = self.place_order(child_topic_id, no_pos, OrderSide.BUY, no_price, current_order_amount)

                                if success:
                                    self.log(f"     ✅ NO 성공 (Order ID: {result})", "SUCCESS")
                                    total_success += 1
                                else:
                                    self.log(f"     ❌ NO 실패: {result}", "ERROR")
                                    total_fail += 1

                                time.sleep(0.5)
                            else:
                                self.log("  ⚠️  NO: noPos 없음, 스킵", "WARNING")
                                total_fail += 1

                    except Exception as e:
                        self.log(f"❌ 거래 실행 중 에러: {e}", "ERROR")
                        import traceback
                        self.log(traceback.format_exc(), "ERROR")
                        total_fail += len(child_list) * 2
                        continue

                self.log("\n" + "=" * 60, "INFO")
                self.log(f"🏁 전체 거래 완료", "INFO")
                self.log(f"   성공: {total_success}", "SUCCESS")
                self.log(f"   실패: {total_fail}", "ERROR")
                self.log("=" * 60, "INFO")

                self.update_status("모든 거래 완료")
                messagebox.showinfo("완료", f"거래 완료\n성공: {total_success}, 실패: {total_fail}")

            except Exception as e:
                self.log(f"❌ 거래 실행 실패: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "ERROR")
                messagebox.showerror("거래 실패", str(e))
            finally:
                self.trade_btn.config(state=NORMAL)
                self.load_btn.config(state=NORMAL)

        threading.Thread(target=trade, daemon=True).start()

    def calculate_safe_price(self, base_price, safe_rate=0.05):
        """SafeRate 적용"""
        price = float(base_price) * (1 + safe_rate)
        if price > 0.999:
            price = 0.999
        elif price < 0.001:
            price = 0.001
        return str(round(price, 3))

    def place_order(self, topic_id, token_id, side, price, order_amount):
        """주문 실행 (SDK 사용)"""
        try:
            # marketId는 정수형이어야 함
            order = PlaceOrderDataInput(
                marketId=int(topic_id),  # ✅ 정수로 변환
                tokenId=token_id,
                side=side,
                orderType=LIMIT_ORDER,
                price=price,
                makerAmountInQuoteToken=order_amount  # ✅ 파라미터로 받은 값 사용
            )

            result = self.client.place_order(order)

            if hasattr(result, 'errno'):
                if result.errno == 0:
                    order_id = result.result.orderData.orderId if hasattr(result.result, 'orderData') else 'N/A'
                    return True, order_id
                else:
                    return False, result.errmsg
            else:
                return True, str(result)

        except Exception as e:
            return False, str(e)

def main():
    root = Tk()
    app = OpinionTradeBot(root)
    root.mainloop()

if __name__ == '__main__':
    main()
