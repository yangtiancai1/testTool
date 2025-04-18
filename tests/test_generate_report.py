from generate_report import generate_report

# 指定模板路径和版本号
version = '9.3.0'

# 调用函数生成报告
output_file = generate_report(version)
print(f'报告生成成功！保存在: {output_file}')