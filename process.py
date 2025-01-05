import os
import re
import json
import logging
from typing import List
from zhipuai import ZhipuAI

# 使用说明：
# 1. 请确保已安装 'zhipuai' 包，可以使用以下命令安装：
#    pip install zhipuai
# 2. 请将 'prompt.txt' 和 'prompt_event.txt' 文件放在与此脚本相同的目录中。
# 3. 请将对话文件 '1.txt' 放在 'E:\\desktop\\project\\qxfx\\shuju_new' 目录下或者自己设置的目录下。
# 4. 点击运行脚本，将自动完成对话分组、第一次分析、合并分析结果、清理Rationale字段、二次分析等操作。
# 注意事项：
# 1. key需要修改为自己创建的key，在zhipuai官网复制即可。
# 2. num需要修改为自己的项目编号，例如：num = 23即为项目编号23，其文件命名为'23.txt',放在文件夹名为'23'的文件夹下。
# 3. 重复写入时如需修改文件名则按照如下形式将新文件名放入大括号'{}'中即可，例如：output_filename = fr"qxfx\shuju_new\{i}\emo_event.json"。
# 4. 修复函数修复后仍错误的内容会保存到错误文件中，文件名为'analysis_result_group{group_number}_error.json'或'emo_event_error.json'，需要进行手动处理。
# 5. 如果最后的event.json中出现重复输出的分析，需要重新运行程序，但无需删除文件，程序会自动覆盖原文件。
# 6. 如果需要修改分组大小，最大tokens数等参数，其默认值为10和4096。因为glm-4-plus模型最大tokens数为4096，并且其输入为10条对话，所以默认值为10和4096。
# 7. 请确保文件夹路径正确，否则会报错，程序会自动创建不存在的文件夹（'output_groups'，'errors'和'ana'）
# 8. 如果出现批量的json文件错误并且无法修复，参照下列内容进行代码修改：
# 1) 元素后内容中出现左引号缺失，如："Sentiment": negative"；则在第115行后插入下列代码： 
#    content = re.sub(r'("Sentiment"\s*:\s*)(\w+)"', r'\1"\2"', content)，将其中的Sentiment修改为出现错误的元素，如：Rationale
# 2) 元素后内容中出现出现右引号缺失，如："Sentiment": negative；则在第115行后插入下列代码：
#    content = re.sub(r'("Rationale"\s*:\s*"[^"]+)(?=\n|,)', r'\1"', content)
#    content = re.sub(r'("Rationale"\s*:\s*)(\w+)"', r'\1"\2"', content)

# 注意！
# 如果出现其他没有列出的问题，请先访问如下网址：https://www.csdn.com。如果没有相应的解决方案，继续访问下列网址：https://www.google.com。
# 或者访问：https://chatgpt.com 或者 https://claude.ai/。
# 如果还是不能解决，打开微信询问'zach'或者'斜方肌也是肌'。


# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局配置
GROUP_SIZE = 10    # 每组对话的数量
MAX_TOKENS = 4096  # 根据ZhipuAI API文档调整
API_MODEL = "glm-4-plus"     # 使用的模型
num = 23       # 项目编号

def group_dialogs_from_file(file_path: str, group_size: int = GROUP_SIZE) -> List[List[str]]:
    """
    从文件中读取对话，并按指定大小进行分组。

    参数:
    - file_path (str): 原始对话文件路径
    - group_size (int): 每组对话的数量

    返回:
    - List[List[str]]: 分组后的对话列表
    """
    if not os.path.exists(file_path):
        logging.error(f"输入文件 '{file_path}' 不存在。")
        return []

    with open(file_path, 'r', encoding='utf-8') as file:
        dialogs = file.readlines()

    dialogs = [dialog.strip() for dialog in dialogs if dialog.strip()]
    grouped_dialogs = [dialogs[i:i + group_size] for i in range(0, len(dialogs), group_size)]
    logging.info(f"总对话数: {len(dialogs)}，分成 {len(grouped_dialogs)} 组。")
    return grouped_dialogs

def save_grouped_dialogs_to_files(grouped_dialogs: List[List[str]], base_output_dir: str):
    """
    将分组后的对话保存到指定目录中。

    参数:
    - grouped_dialogs (List[List[str]]): 分组后的对话
    - base_output_dir (str): 输出文件夹的根目录
    """
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
        logging.info(f"创建目录 '{base_output_dir}'。")

    for idx, group in enumerate(grouped_dialogs, start=1):
        output_file_path = os.path.join(base_output_dir, f"group_{idx}.txt")
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(f"第{idx}组对话：\n")
            for dialog in group:
                file.write(f"{dialog}\n")
            file.write("\n")  # 换行分隔每组
        logging.info(f"已保存第 {idx} 组到 '{output_file_path}'。")
    logging.info(f"分组后的对话已保存到 {base_output_dir} 文件夹中。")

def strip_markdown_code(content: str) -> str:
    """
    移除字符串中的Markdown代码块标记。

    参数:
    - content (str): 原始字符串

    返回:
    - str: 移除Markdown标记后的字符串
    """
    # 移除开头的 ```json 和结尾的 ```
    content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'```$', '', content, flags=re.MULTILINE)
    return content.strip()

def fix_json(content: str) -> str:
    """
    尝试修复错误的JSON字符串，特别是针对以下问题：
    1. 字符串值缺少结束引号。
    2. 字符串值未被引号包围。

    参数:
    - content (str): 原始字符串

    返回:
    - str: 修复后的字符串
    """
    # 替换单引号为双引号
    content = content.replace("'", '"')

    # 修复 Sentiment 字段缺少引号的问题
    # 将 "Sentiment": negative", 修复为 "Sentiment": "negative",
    content = re.sub(r'("Sentiment"\s*:\s*)(\w+)"', r'\1"\2"', content)
    # 将 "Rationale": neutral", 修复为 "Sentiment": "neutral",
    content = re.sub(r'("Rationale"\s*:\s*)(\w+)"', r'\1"\2"', content)

    # 修复 Rationale 字段缺少结束引号的问题
    # 将 "Rationale": "因为...态度 修复为 "Rationale": "因为...态度"
    content = re.sub(r'("Rationale"\s*:\s*"[^"]+)(?=\n|,)', r'\1"', content)
    content = re.sub(r'("Rationale"\s*:\s*)(\w+)"', r'\1"\2"', content)

    # Enclose unquoted string values in quotes
    # 例如： "Sentiment": negative,
    # 查找 "Key": value, 其中 value 是非数字且未被引号包围
    content = re.sub(r'("Sentiment"\s*:\s*)([a-zA-Z]+)(\s*[,\n}])', r'\1"\2"\3', content)
    content = re.sub(r'("Rationale"\s*:\s*)([a-zA-Z]+)(\s*[,\n}])', r'\1"\2"\3', content)

    # 移除多余的逗号，例如在对象或数组的最后一个元素后
    content = re.sub(r',\s*([}\]])', r'\1', content)

    # 平衡花括号和方括号
    open_braces = content.count('{') - content.count('}')
    open_brackets = content.count('[') - content.count(']')

    if open_braces > 0:
        content += '}' * open_braces
    elif open_braces < 0:
        content = '{' * (-open_braces) + content

    if open_brackets > 0:
        content += ']' * open_brackets
    elif open_brackets < 0:
        content = '[' * (-open_brackets) + content

    return content

def analyze_and_store_primary(j: int, group_number: int, api_key: str, prompt_content: str, 
                             model: str = API_MODEL, max_tokens: int = MAX_TOKENS):
    """
    调用ZhipuAI API对分组对话进行分析，并将结果保存为JSON文件。

    参数:
    - j (int): 项目编号
    - group_number (int): 对话组编号
    - api_key (str): ZhipuAI API密钥
    - prompt_content (str): 系统提示内容
    - model (str): 使用的模型
    - max_tokens (int): 最大tokens数
    """
    input_filename = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), "output_groups", f"group_{group_number}.txt")
    output_filename = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), "ana", f"analysis_result_group{group_number}.json")

    if not os.path.exists(input_filename):
        logging.error(f"文件 '{input_filename}' 不存在。")
        return

    # 确保 'ana' 目录存在
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    with open(input_filename, "r", encoding="utf-8") as file:
        input_text = file.read()

    client = ZhipuAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": input_text}
            ],
            top_p=0.7,
            temperature=0.9,
            max_tokens=max_tokens,
            stream=False
        )
    except Exception as e:
        logging.error(f"调用 API 进行第 {group_number} 组分析时出错: {e}")
        return

    if response and hasattr(response, 'choices'):
        for choice in response.choices:
            message = getattr(choice, 'message', None)
            content = getattr(message, 'content', None)
            if content:
                # 移除Markdown代码块标记
                clean_content = strip_markdown_code(content)
                logging.debug(f"Clean content for group {group_number}: {clean_content}")  # 添加调试日志
                try:
                    # 尝试解析JSON
                    analysis = json.loads(clean_content)
                    # 如果成功，直接写入文件
                    with open(output_filename, "w", encoding="utf-8") as file:
                        json.dump(analysis, file, ensure_ascii=False, indent=4)
                    logging.info(f"第 {group_number} 组的分析结果已保存到 '{output_filename}'。")
                except json.JSONDecodeError as jde:
                    logging.error(f"第一次解析JSON时出错: {jde}")
                    logging.error(f"原始内容: {clean_content}")
                    # 尝试修复JSON
                    fixed_content = fix_json(clean_content)
                    try:
                        analysis_fixed = json.loads(fixed_content)
                        with open(output_filename, "w", encoding="utf-8") as file:
                            json.dump(analysis_fixed, file, ensure_ascii=False, indent=4)
                        logging.info(f"第 {group_number} 组的分析结果（修复后）已保存到 '{output_filename}'。")
                    except json.JSONDecodeError as jde_fixed:
                        logging.error(f"修复后解析JSON时出错: {jde_fixed}")
                        logging.error(f"修复后的内容: {fixed_content}")
                        # 可选：将无法修复的内容保存到错误文件中
                        error_output_filename = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), "errors", f"analysis_result_group{group_number}_error.json")
                        os.makedirs(os.path.dirname(error_output_filename), exist_ok=True)
                        with open(error_output_filename, "w", encoding="utf-8") as error_file:
                            error_file.write(clean_content)
                        logging.info(f"无法修复的分析结果已保存到 '{error_output_filename}'。")
    else:
        logging.error(f"API响应中没有'choices'字段或'choices'为空。")

def natural_sort_key(s: str) -> List:
    """自然排序的键函数"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def combine_and_clean_files(input_folder: str, output_file: str) -> bool:
    """
    合并指定文件夹中的所有JSON文件。

    参数:
    - input_folder (str): 输入文件夹路径
    - output_file (str): 输出文件路径

    返回:
    - bool: 是否成功
    """
    if not os.path.exists(input_folder):
        logging.error(f"文件夹 '{input_folder}' 不存在！")
        return False

    try:
        all_content = []
        files = os.listdir(input_folder)
        json_files = [f for f in files if f.lower().endswith('.json')]

        if not json_files:
            logging.warning(f"在 '{input_folder}' 中没有找到JSON文件!")
            return False

        # 按自然顺序排序文件
        files_sorted = sorted(json_files, key=natural_sort_key)

        for json_file in files_sorted:
            file_path = os.path.join(input_folder, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_content.extend(data)
                    elif isinstance(data, dict):
                        all_content.append(data)
                    else:
                        logging.warning(f"文件 '{json_file}' 的内容格式不支持。")
                logging.info(f"已处理: {json_file}")
            except Exception as e:
                logging.warning(f"处理文件 '{json_file}' 时出错: {str(e)}")
                continue

        # 写入输出文件
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_content, f, ensure_ascii=False, indent=4)

        logging.info(f"\n成功! 所有文件已合并到: {output_file}")
        logging.info(f"共处理了 {len(json_files)} 个文件")
        return True

    except Exception as e:
        logging.error(f"错误: 处理过程中出现异常: {str(e)}")
        return False

def clean_rationale(rationale: str) -> str:
    """
    清理 Rationale 字段：
    - 删除 "所以" 到字符串结束的内容，包括 "所以"
    - 删除 "因为" 这个词

    参数:
    - rationale (str): 原始Rationale内容

    返回:
    - str: 清理后的Rationale内容
    """
    if not rationale:
        return rationale  # 如果为空或None，直接返回
    # 删除 "所以" 到字符串结束的内容，包括 "所以"
    rationale = re.sub(r"所以.*", "", rationale)
    # 删除 "因为" 这个词
    rationale = re.sub(r"因为", "", rationale)
    return rationale.strip()

def process_json_file(input_file: str, output_file: str):
    """
    处理输入的 JSON 文件，清理 Rationale 字段，输出处理后的 JSON 文件。

    参数:
    - input_file (str): 输入JSON文件路径
    - output_file (str): 输出JSON文件路径
    """
    if not os.path.exists(input_file):
        logging.error(f"输入 JSON 文件 '{input_file}' 不存在。")
        return
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for record in data:
            if "Rationale" in record:
                record["Rationale"] = clean_rationale(record.get("Rationale", ""))

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info(f"处理完成，清理后的文件已保存到: {output_file}")
    except Exception as e:
        logging.error(f"处理 JSON 文件时出错: {e}")

def analyze_and_store_secondary(i: int, api_key: str, prompt_content: str, 
                                model: str = API_MODEL, max_tokens: int = MAX_TOKENS):
    """
    调用ZhipuAI API对清理后的JSON文件进行二次分析，并保存结果。

    参数:
    - i (int): 项目编号
    - api_key (str): ZhipuAI API密钥
    - prompt_content (str): 系统提示内容
    - model (str): 使用的模型
    - max_tokens (int): 最大tokens数
    """
    input_filename = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(i), f"chat_{num}.json")
    output_filename = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(i), f"emo_event_{num}.json")

    if not os.path.exists(input_filename):
        logging.error(f"文件 '{input_filename}' 不存在。")
        return

    with open(input_filename, "r", encoding="utf-8") as file:
        input_text = file.read()

    client = ZhipuAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": input_text}
            ],
            top_p=0.7,
            temperature=0.9,
            max_tokens=max_tokens,
            stream=False
        )
    except Exception as e:
        logging.error(f"调用 API 进行二次分析时出错: {e}")
        return

    if response and hasattr(response, 'choices'):
        for choice in response.choices:
            message = getattr(choice, 'message', None)
            content = getattr(message, 'content', None)
            if content:
                # 移除Markdown代码块标记
                clean_content = strip_markdown_code(content)
                logging.debug(f"Clean content for secondary analysis: {clean_content}")  # 添加调试日志
                try:
                    # 尝试解析JSON
                    analysis = json.loads(clean_content)
                    # 如果成功，直接写入文件
                    with open(output_filename, "w", encoding="utf-8") as file:
                        json.dump(analysis, file, ensure_ascii=False, indent=4)
                    logging.info(f"二次分析结果已保存到 '{output_filename}'。")
                except json.JSONDecodeError as jde:
                    logging.error(f"第一次解析JSON时出错: {jde}")
                    logging.error(f"原始内容: {clean_content}")
                    # 尝试修复JSON
                    fixed_content = fix_json(clean_content)
                    try:
                        analysis_fixed = json.loads(fixed_content)
                        with open(output_filename, "w", encoding="utf-8") as file:
                            json.dump(analysis_fixed, file, ensure_ascii=False, indent=4)
                        logging.info(f"二次分析结果（修复后）已保存到 '{output_filename}'。")
                    except json.JSONDecodeError as jde_fixed:
                        logging.error(f"修复后解析JSON时出错: {jde_fixed}")
                        logging.error(f"修复后的内容: {fixed_content}")
                        # 可选：将无法修复的内容保存到错误文件中
                        error_output_filename = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(i), "errors", f"emo_event_error.json")
                        os.makedirs(os.path.dirname(error_output_filename), exist_ok=True)
                        with open(error_output_filename, "w", encoding="utf-8") as error_file:
                            error_file.write(clean_content)
                        logging.info(f"无法修复的二次分析结果已保存到 '{error_output_filename}'。")
    else:
        logging.error(f"API响应中没有'choices'字段或'choices'为空。")

def read_prompt(file_path: str) -> str:
    """
    读取提示文件内容。

    参数:
    - file_path (str): 提示文件路径

    返回:
    - str: 提示内容
    """
    if not os.path.exists(file_path):
        logging.error(f"提示文件 '{file_path}' 不存在。")
        return ""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content

def main():
    try:
        # 配置项目编号
        j = num  # 主分析步骤
        i_secondary = num  # 二次分析步骤，通常与j相同

        # 获取API密钥
        api_key = "15c5a08cff8b4ea8bd888f54c33b240b.8cRCAwiqnd7RGzpk"  # 建议使用环境变量管理API密钥
        if not api_key:
            logging.error("未找到 API 密钥。请设置环境变量 'ZHIPUAI_API_KEY'。")
            return

        # Step 1: 分组对话
        input_file = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", f"{j}.txt")
        output_groups_dir = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), "output_groups")
        grouped_dialogs = group_dialogs_from_file(input_file, group_size=GROUP_SIZE)
        if not grouped_dialogs:
            logging.error("没有对话可处理。")
            return
        save_grouped_dialogs_to_files(grouped_dialogs, output_groups_dir)

        # Step 2: 第一次分析
        prompt_content = read_prompt("prompt.txt")
        if not prompt_content:
            logging.error("提示内容为空。")
            return
        for group_num in range(1, len(grouped_dialogs) + 1):
            analyze_and_store_primary(j, group_num, api_key, prompt_content)

        # Step 3: 合并分析结果
        analyze_results_dir = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), "ana")
        combined_file = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), "combined_output.json")
        combine_success = combine_and_clean_files(analyze_results_dir, combined_file)
        if not combine_success:
            logging.error("合并分析结果失败。")
            return

        # Step 4: 清理Rationale字段
        final_json = os.path.join("E:\\desktop\\project\\qxfx\\shuju_new", str(j), f"chat_{num}.json")
        process_json_file(combined_file, final_json)

        # Step 5: 二次分析
        prompt_event_content = read_prompt("prompt_event.txt")
        if not prompt_event_content:
            logging.error("事件提示内容为空。")
            return
        analyze_and_store_secondary(i_secondary, api_key, prompt_event_content)

    except Exception as e:
        logging.error(f"程序执行过程中出错: {e}", exc_info=True)

if __name__ == "__main__":
    main()
