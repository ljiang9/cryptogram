"""cryptogram - 替换密码解谜小游戏。

随机挑选一句名言，用单表替换密码加密，玩家通过猜测字母映射逐字破解。
纯标准库：argparse / sys / random。
"""

import argparse
import random
import sys

# 内置名言（约 30 条）：选用公有领域/流传广泛的短句，避免现代版权文本。
QUOTES = [
    ("To be or not to be, that is the question.", "William Shakespeare"),
    ("I think, therefore I am.", "Rene Descartes"),
    ("Knowledge is power.", "Francis Bacon"),
    ("Time is money.", "Benjamin Franklin"),
    ("Actions speak louder than words.", "Proverb"),
    ("A journey of a thousand miles begins with a single step.", "Laozi"),
    ("The unexamined life is not worth living.", "Socrates"),
    ("All that glitters is not gold.", "William Shakespeare"),
    ("Where there is a will, there is a way.", "Proverb"),
    ("No pain, no gain.", "Proverb"),
    ("Practice makes perfect.", "Proverb"),
    ("Honesty is the best policy.", "Proverb"),
    ("Better late than never.", "Proverb"),
    ("The early bird catches the worm.", "Proverb"),
    ("A friend in need is a friend indeed.", "Proverb"),
    ("Do unto others as you would have them do unto you.", "Golden Rule"),
    ("The pen is mightier than the sword.", "Edward Bulwer-Lytton"),
    ("What does not kill me makes me stronger.", "Friedrich Nietzsche"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Stay hungry, stay foolish.", "Stewart Brand"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
    ("The best time to plant a tree was twenty years ago.", "Proverb"),
    ("A picture is worth a thousand words.", "Proverb"),
    ("Fortune favors the bold.", "Latin proverb"),
    ("When in Rome, do as the Romans do.", "Proverb"),
    ("Two heads are better than one.", "Proverb"),
    ("The grass is always greener on the other side.", "Proverb"),
    ("Do not count your chickens before they hatch.", "Proverb"),
    ("A rolling stone gathers no moss.", "Proverb"),
    ("The proof of the pudding is in the eating.", "Proverb"),
]

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_key(rng):
    """生成随机替换密钥：明文字母 -> 密文字母的置换。"""
    shuffled = list(ALPHA)
    rng.shuffle(shuffled)
    return dict(zip(ALPHA, shuffled))


def encrypt(text, key):
    """用密钥加密：保持大小写和标点。"""
    out = []
    for ch in text:
        up = ch.upper()
        if up in key:
            enc = key[up]
            out.append(enc if ch.isupper() else enc.lower())
        else:
            out.append(ch)
    return "".join(out)


def frequency(text):
    """统计密文中各字母出现次数（降序）。"""
    counts = {}
    for ch in text.upper():
        if ch in ALPHA:
            counts[ch] = counts.get(ch, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def render(cipher_text, mapping):
    """按当前猜测映射渲染解码进度。mapping: 密文字母 -> 猜测的明文字母。"""
    out = []
    for ch in cipher_text:
        up = ch.upper()
        if up in mapping:
            plain = mapping[up]
            out.append(plain if ch.isupper() else plain.lower())
        elif up in ALPHA:
            out.append("_")
        else:
            out.append(ch)
    return "".join(out)


def solved(cipher_text, mapping, key):
    """当前映射是否完全正确（所有出现的密文字母都猜对）。"""
    letters = {c.upper() for c in cipher_text if c.upper() in ALPHA}
    if not letters <= set(mapping):
        return False
    inv = {v: k for k, v in key.items()}  # 密文字母 -> 真实明文字母
    return all(mapping[c] == inv[c] for c in letters)


def play_interactive(cipher_text, key):
    mapping = {}  # 密文字母 -> 玩家猜测的明文字母
    print("=" * 56)
    print("密文：")
    print(cipher_text)
    print("=" * 56)
    print("命令：猜 A=T（把密文 A 猜成明文 T）/ freq（字母频率）/ 撤回 A / 放弃 / 退出")
    print()
    while True:
        print("当前进度：")
        print(render(cipher_text, mapping))
        print()
        try:
            line = input("你的猜测> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return 1
        if not line:
            continue
        low = line.lower()
        if low in ("退出", "quit", "q", "exit"):
            print("已退出。")
            return 1
        if low in ("放弃", "giveup", "reveal"):
            print("答案揭晓：密钥是", " ".join(f"{k}->{v}" for k, v in sorted(key.items())))
            inv = {v: k for k, v in key.items()}
            print("原文：", render(cipher_text, inv))
            return 1
        if low in ("freq", "频率"):
            print("密文字母频率：", " ".join(f"{c}:{n}" for c, n in frequency(cipher_text)))
            print("（英语里 E T A O I N 最常见，可作切入点）")
            continue
        if low.startswith("撤回"):
            c = line[2:].strip().upper()
            if c in mapping:
                del mapping[c]
                print(f"已撤回 {c} 的猜测。")
            else:
                print("没有这个字母的猜测。")
            continue
        # 解析 "猜 A=T" / "A=T" / "A T"（去掉可选的"猜"前缀）
        body = line[1:].strip() if line.startswith("猜") else line
        guess = body.upper().replace("=", " ").split()
        if len(guess) == 2 and len(guess[0]) == 1 and len(guess[1]) == 1 \
                and guess[0] in ALPHA and guess[1] in ALPHA:
            c, p = guess
            mapping[c] = p
            # 冲突提醒：两个密文字母猜成同一个明文字母
            rev = {}
            for cc, pp in mapping.items():
                rev.setdefault(pp, []).append(cc)
            if len(rev[p]) > 1:
                print(f"注意：{', '.join(rev[p])} 都被猜成了 {p}，其中至多一个是对的。")
            if solved(cipher_text, mapping, key):
                print()
                print("🎉 全部破解！原文：")
                print(render(cipher_text, mapping))
                return 0
        else:
            print("格式不对。用「猜 A=T」这样的格式，或输入 freq 看频率。")


def main(argv=None):
    ap = argparse.ArgumentParser(description="cryptogram - 替换密码解谜小游戏")
    ap.add_argument("--seed", type=int, default=None, help="随机种子（可复现同一谜题）")
    ap.add_argument("--quote", type=int, default=None, help="指定名言编号（0 起）")
    ap.add_argument("--reveal", action="store_true", help="直接显示谜题和答案（非交互）")
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    if args.quote is not None:
        if not 0 <= args.quote < len(QUOTES):
            print(f"quote 编号超出范围（0-{len(QUOTES) - 1}）", file=sys.stderr)
            return 2
        text, author = QUOTES[args.quote]
    else:
        text, author = rng.choice(QUOTES)
    key = make_key(rng)
    cipher_text = encrypt(text, key)

    if args.reveal:
        print("密文：", cipher_text)
        print("作者：", author)
        print("答案：", text)
        print("密钥：", " ".join(f"{k}->{v}" for k, v in sorted(key.items())))
        return 0

    if not sys.stdin.isatty():
        print("交互模式需要终端。请用 --reveal 直接看谜题答案。", file=sys.stderr)
        return 2
    print(f"（作者：{author}，共 {len(QUOTES)} 条名言中的一条）")
    return play_interactive(cipher_text, key)


if __name__ == "__main__":
    sys.exit(main())
