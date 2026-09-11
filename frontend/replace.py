with open('org_output.html', 'r', encoding='utf-8') as f:
    org_html = f.read()

with open(r'c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\views\employees\OrganizationView.vue', 'r', encoding='utf-8') as f:
    vue = f.read()

s1 = '<div class="org-chart '
s2 = '<!-- Modal d\'affectation -->'

if s1 in vue and s2 in vue:
    out = vue[:vue.index(s1)] + '<div class="org-chart relative w-full overflow-auto h-[80vh] flex justify-center items-start pt-10">\n<div class="relative w-[1700px] h-[1000px] shrink-0">\n' + org_html + '\n</div>\n</div>\n\n</div>\n</div>\n\n    ' + vue[vue.index(s2):]
    with open(r'c:\Users\adam.guizaoui\Desktop\ERP\frontend\src\views\employees\OrganizationView.vue', 'w', encoding='utf-8') as f:
        f.write(out)
    print('SUCCESS')
else:
    print('FAILED TO FIND STRINGS')
