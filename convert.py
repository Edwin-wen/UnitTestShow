#!/usr/bin/env python3
import shutil
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

xml_dir = Path.cwd() / "xml"
xslt_path =  Path.cwd() / "gtest2html" / "gtest2html.xslt"
html_dir = Path.cwd() / 'html'
template_dir = Path.cwd()  / 'template'
index_path = template_dir / "tem_index.html"
card_template_path = template_dir / "tem_card.html"
failures_template_path = template_dir / "tem_failpage.html"


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='将gtest XML结果转换为HTML报告')
    parser.add_argument('gtest_result', help='gtest结果输出目录（包含XML文件）')
    parser.add_argument('--html-dir', '-o' , help='转换后的HTML输出目录')
    parser.add_argument('--xslt-file', '-x', help='XSLT样式文件路径')
    parser.add_argument('--template-dir', '-t', help='HTML模板文件路径')
    args = parser.parse_args()

    # 验证输入目录和文件是否存在
    global xml_dir, xslt_path, html_dir, template_dir, index_path, card_template_path, failures_template_path
    if args.gtest_result:
        xml_dir = Path(args.gtest_result)
    if args.xslt_file:
        xslt_path = Path(args.xslt_file)
    if args.html_dir:
        html_dir = Path(args.html_dir)
    if args.template_dir:
        template_dir = Path(args.template_dir)
    index_path = template_dir / "tem_index.html"
    card_template_path = template_dir / "tem_card.html"
    failures_template_path = template_dir / "tem_failpage.html"

    try:
        shutil.rmtree(html_dir)  # 递归删除目录
        print(f"成功删除目录: {html_dir}")
    except OSError as e:
        print(f"错误: {e}")

    if not xml_dir.is_dir():
        print(f"错误: 结果目录 '{xml_dir}' 不存在或不是目录")
        sys.exit(1)

    if not xslt_path.is_file():
        print(f"错误: XSLT文件 '{xslt_path}' 不存在或不是文件")
        sys.exit(1)

    if not index_path.is_file():
        print(f"错误: 模板文件 '{index_path}' 不存在或不是文件")
        sys.exit(1)

    if not card_template_path.is_file():
        print(f"错误: 卡片模板文件 '{card_template_path}' 不存在或不是文件")
        sys.exit(1)

    if not failures_template_path.is_file():
        print(f"错误: 失败案例页面模板文件 '{failures_template_path}' 不存在或不是文件")
        sys.exit(1)

    # 创建HTML输出目录（如果不存在）
    html_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有XML文件
    xml_files = list(xml_dir.glob('*.xml'))
    if not xml_files:
        print(f"警告: 在目录 '{xml_dir}' 中未找到XML文件")
        sys.exit(0)

    # 转换XML文件为HTML
    html_files = []
    for xml_file in xml_files:
        html_file = html_dir / f"{xml_file.stem}.html"
        try:
            convert_xml_to_html(xml_file, html_file, xslt_path)
            html_files.append(html_file)
            print(f"成功转换: {xml_file} -> {html_file}")
        except subprocess.CalledProcessError as e:
            print(f"错误: 转换 {xml_file} 时出错: {e}")
            continue

    # 生成索引页面
    if html_files:
        generate_index_page(html_files, html_dir / "index.html", index_path, card_template_path, xml_files, failures_template_path)
        print(f"成功生成索引页: {html_dir / 'index.html'}")
    else:
        print("错误: 没有成功转换任何文件，无法生成索引页")


def convert_xml_to_html(xml_file, html_file, xslt_file):
    """使用xsltproc将XML文件转换为HTML"""
    try:
        # 执行xsltproc命令
        subprocess.run(
            ['xsltproc', '-o', str(html_file), str(xslt_file), str(xml_file)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        # 打印详细的错误信息
        print(f"执行命令失败: {' '.join(e.cmd)}")
        print(f"标准输出: {e.stdout.decode('utf-8')}")
        print(f"标准错误: {e.stderr.decode('utf-8')}")
        raise


def generate_index_page(html_files, index_file, template_file, card_template_file, xml_files, failures_template_path):
    """生成包含所有HTML报告链接的索引页面，使用指定的模板文件"""
    # 创建HTML文件与XML文件的映射
    html_to_xml = {}
    for html_file in html_files:
        base_name = html_file.stem
        # 查找对应的XML文件
        for xml_file in xml_files:
            if xml_file.stem == base_name:
                html_to_xml[html_file] = xml_file
                break

    # 排序HTML文件（按名称）
    html_files.sort(key=lambda x: x.name)

    # 读取模板文件内容
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # 读取卡片模板文件内容
    with open(card_template_file, 'r', encoding='utf-8') as f:
        card_template = f.read()

    # 收集测试信息和失败案例
    test_suites = []
    all_failures = []

    for html_file in html_files:
        # 初始化测试信息
        tests = '未知'
        failures = '未知'
        errors = '未知'
        time = '未知'
        suite_name = html_file.stem

        # 尝试从对应的XML文件中提取测试信息
        xml_file = html_to_xml.get(html_file)
        if xml_file:
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # 获取测试套件信息
                if root.tag == 'testsuites':
                    # 处理testsuites根元素
                    tests = root.get('tests', '未知')
                    failures = root.get('failures', '未知')
                    errors = root.get('errors', '未知')
                    time = root.get('time', '未知')

                    # 收集所有失败案例
                    for testsuite in root.findall('testsuite'):
                        suite_name_inner = testsuite.get('name', '未知套件')
                        for testcase in testsuite.findall('testcase'):
                            for failure in testcase.findall('failure'):
                                all_failures.append({
                                    'suite_name': suite_name_inner,
                                    'test_name': testcase.get('name', '未知测试'),
                                    'time': testcase.get('time', '未知'),
                                    'message': failure.get('message', '未知错误'),
                                    'type': failure.get('type', '未知类型'),
                                    'content': failure.text.strip() if failure.text else '无详细信息',
                                    'html_file': html_file.name
                                })
                elif root.tag == 'testsuite':
                    # 处理单个testsuite
                    tests = root.get('tests', '未知')
                    failures = root.get('failures', '未知')
                    errors = root.get('errors', '未知')
                    time = root.get('time', '未知')
                    suite_name = root.get('name', suite_name)

                    # 收集所有失败案例
                    for testcase in root.findall('testcase'):
                        for failure in testcase.findall('failure'):
                            all_failures.append({
                                'suite_name': suite_name,
                                'test_name': testcase.get('name', '未知测试'),
                                'time': testcase.get('time', '未知'),
                                'message': failure.get('message', '未知错误'),
                                'type': failure.get('type', '未知类型'),
                                'content': failure.text.strip() if failure.text else '无详细信息',
                                'html_file': html_file.name
                            })

                # 转换时间格式（如果可能）
                if time != '未知':
                    try:
                        time_float = float(time)
                        if time_float < 1:
                            time = f"{time_float * 1000:.1f}ms"
                        else:
                            time = f"{time_float:.2f}s"
                    except ValueError:
                        pass
            except Exception as e:
                print(f"警告: 无法从 {xml_file} 中提取测试信息: {e}")

        # 计算通过率
        if tests != '未知' and failures != '未知':
            try:
                tests_num = int(tests)
                failures_num = int(failures)
                if tests_num > 0:
                    pass_rate = f"{((tests_num - failures_num) / tests_num * 100):.1f}%"
                else:
                    pass_rate = "100%"
            except ValueError:
                pass_rate = '未知'
        else:
            pass_rate = '未知'

        # 设置状态样式
        if failures == '0' or (failures != '未知' and int(failures) == 0):
            status_color = 'success'
            status_text = '全部通过'
            status_icon = 'check-circle'
        elif failures == '未知':
            status_color = 'neutral'
            status_text = '状态未知'
            status_icon = 'question-circle'
        else:
            status_color = 'danger'
            status_text = f'失败 {failures} 个'
            status_icon = 'exclamation-circle'

        # 添加到测试套件列表
        test_suites.append({
            'suite_name': suite_name,
            'tests': tests,
            'failures': failures,
            'errors': errors,
            'time': time,
            'pass_rate': pass_rate,
            'status_color': status_color,
            'status_text': status_text,
            'status_icon': status_icon,
            'html_file': html_file.name,
            'failure_count': int(failures) if failures != '未知' else 0
        })

    # 计算总体统计信息
    total_tests = 0
    total_success = 0
    total_failures = 0
    total_errors = 0
    total_time = 0.0
    valid_suites = 0

    for suite in test_suites:
        if suite['tests'] != '未知' and suite['failures'] != '未知' and suite['errors'] != '未知':
            valid_suites += 1
            total_tests += int(suite['tests'])
            total_failures += int(suite['failures'])
            total_errors += int(suite['errors'])
            if suite['time'] != '未知' and 's' in suite['time']:
                total_time += float(suite['time'].replace('s', ''))

    total_success = total_tests - total_failures
    if total_tests > 0:
        overall_pass_rate = f"{(total_success / total_tests * 100):.1f}%"
    else:
        overall_pass_rate = "100%"



    # 设置总体状态
    if total_failures == 0 and valid_suites > 0:
        overall_status_color = 'success'
        overall_status_text = '全部通过'
        overall_status_icon = 'check-circle'
    elif valid_suites == 0:
        overall_status_color = 'neutral'
        overall_status_text = '状态未知'
        overall_status_icon = 'question-circle'
    else:
        overall_status_color = 'danger'
        overall_status_text = f'失败 {total_failures} 个'
        overall_status_icon = 'exclamation-circle'

    # 生成卡片HTML
    cards_html = ""
    for suite in test_suites:
        # 填充卡片模板
        card_html = card_template
        card_html = card_html.replace('{{suite_name}}', suite['suite_name'])
        card_html = card_html.replace('{{tests}}', suite['tests'])

        # 为失败数量添加链接
        failure_link = f'<a href="failures.html?suite={suite["suite_name"]}" class="hover:underline text-{suite["status_color"]}">{suite["failures"]}</a>' if \
        suite['failure_count'] > 0 else suite['failures']
        card_html = card_html.replace('{{failures}}', failure_link)

        card_html = card_html.replace('{{errors}}', suite['errors'])
        card_html = card_html.replace('{{time}}', suite['time'])
        card_html = card_html.replace('{{pass_rate}}', suite['pass_rate'])
        card_html = card_html.replace('{{status_color}}', suite['status_color'])
        card_html = card_html.replace('{{status_text}}', suite['status_text'])
        card_html = card_html.replace('{{status_icon}}', suite['status_icon'])
        card_html = card_html.replace('{{html_file}}', suite['html_file'])

        cards_html += card_html

    # 替换模板中的变量
    filled_content = template_content
    filled_content = filled_content.replace('{{generation_time}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    filled_content = filled_content.replace('{{total_reports}}', str(len(test_suites)))
    filled_content = filled_content.replace('{{total_tests}}', str(total_tests))
    filled_content = filled_content.replace('{{total_success}}', str(total_success))

    # 为总失败数量添加链接
    total_failure_link = f'<a href="failures.html" class="hover:underline text-{overall_status_color}">{total_failures}</a>' if total_failures > 0 else str(
        total_failures)
    filled_content = filled_content.replace('{{total_failures}}', total_failure_link)

    filled_content = filled_content.replace('{{total_errors}}', str(total_errors))
    filled_content = filled_content.replace('{{total_time}}', f"{total_time:.2f}s")
    filled_content = filled_content.replace('{{overall_pass_rate}}', overall_pass_rate)
    filled_content = filled_content.replace('{{overall_status_color}}', overall_status_color)
    filled_content = filled_content.replace('{{overall_status_text}}', overall_status_text)
    filled_content = filled_content.replace('{{overall_status_icon}}', overall_status_icon)
    filled_content = filled_content.replace('{{report_cards}}', cards_html)

    # 写入索引文件
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(filled_content)

    # 生成失败案例页面
    generate_failures_page(all_failures, html_dir / "failures.html", template_file, failures_template_path)


def generate_failures_page(all_failures, output_file, template_file, failures_template_file):
    """生成失败案例汇总页面"""
    # 如果没有失败案例，生成空页面
    if not all_failures:
        return

    # 读取模板文件内容
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # 读取失败案例页面模板文件内容
    with open(failures_template_file, 'r', encoding='utf-8') as f:
        failures_page_template = f.read()

    # 按套件分组失败案例
    failures_by_suite = {}
    for failure in all_failures:
        suite_name = failure['suite_name']
        if suite_name not in failures_by_suite:
            failures_by_suite[suite_name] = []
        failures_by_suite[suite_name].append(failure)

    # 生成失败案例内容
    failures_content = ""
    for suite_name, suite_failures in failures_by_suite.items():
        suite_content = f"""
            <div class="mb-6">
                <h3 class="text-xl font-semibold text-neutral-700 mb-3 flex items-center">
                    <i class="fa fa-cubes text-danger mr-2"></i>
                    {suite_name}
                    <span class="ml-2 text-sm bg-danger/10 text-danger px-2 py-0.5 rounded-full">
                        {len(suite_failures)} 个失败
                    </span>
                </h3>
                <div class="space-y-4">
        """

        for failure in suite_failures:
            # 为测试名称添加链接，指向完整报告中的特定测试
            test_link = f"<a href=\"{failure['html_file']}#{failure['suite_name']}.{failure['test_name']}\" class=\"hover:underline text-primary\">{failure['test_name']}</a>"

            suite_content += f"""
                    <div class="bg-white rounded-lg shadow-md overflow-hidden border-l-4 border-danger">
                        <div class="p-4">
                            <div class="flex justify-between items-start mb-3">
                                <h4 class="font-medium text-neutral-800">{test_link}</h4>
                                <span class="text-xs text-neutral-500">耗时: {failure['time']}s</span>
                            </div>
                            <div class="mb-3 text-sm">
                                <span class="font-medium text-neutral-600">错误类型:</span>
                                <span class="text-danger">{failure['type']}</span>
                            </div>
                            <div class="mb-3 text-sm">
                                <span class="font-medium text-neutral-600">错误信息:</span>
                                <span>{failure['message']}</span>
                            </div>
                            <div class="bg-gray-50 p-3 rounded text-xs text-neutral-700 max-h-40 overflow-y-auto">
                                <pre class="whitespace-pre-wrap">{failure['content']}</pre>
                            </div>
                        </div>
                    </div>
            """

        suite_content += """
                </div>
            </div>
        """
        failures_content += suite_content

    # 替换失败案例页面模板中的变量
    filled_failures_content = failures_page_template
    filled_failures_content = filled_failures_content.replace('{{generation_year}}', str(datetime.now().year))
    filled_failures_content = filled_failures_content.replace('{{total_failures}}', str(len(all_failures)))
    filled_failures_content = filled_failures_content.replace('{{total_suites}}', str(len(failures_by_suite)))
    filled_failures_content = filled_failures_content.replace('{{failures_content}}', failures_content)

    # 写入失败案例页面
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(filled_failures_content)


if __name__ == "__main__":
    main()    