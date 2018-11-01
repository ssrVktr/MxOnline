from django.shortcuts import render
from django.views.generic.base import View
from django.http import JsonResponse
from django.db.models import Q
from .models import CourseOrg, CityDict, Teacher
from .forms import UserAskForm
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from operation.models import UserFavorite


class OrgView(View):
    def get(self, request):
        # 查找到所有的课程机构
        all_orgs = CourseOrg.objects.all()
        # 取出排名前三的热门机构
        hot_orgs = all_orgs.order_by('-click_nums')[:3]
        # 取出所有的城市
        all_citys = CityDict.objects.all()
        # 搜索功能
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_orgs = all_orgs.filter(
                Q(name__icontains=search_keywords) |
                Q(desc__icontains=search_keywords)
            )
        # 按城市筛选
        try:
            city_id = int(request.GET.get('city', ''))
        except ValueError:
            city_id = ''
        if city_id:
            all_orgs = all_orgs.filter(city_id=city_id)
        # 按机构类别筛选
        category = request.GET.get('ct', '')
        if category:
            all_orgs = all_orgs.filter(category=category)
        # 排序
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'students':
                all_orgs = all_orgs.order_by('-students')
            elif sort == 'courses':
                all_orgs = all_orgs.order_by('-course_nums')

        # 对课程机构进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', '1')
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_orgs, 5, request=request)
        orgs = p.page(page)
        # 总共有多少家机构使用count进行统计
        org_numbers = all_orgs.count()
        return render(request, 'org-list.html', {
            'all_orgs': orgs,
            'hot_orgs': hot_orgs,
            'all_citys': all_citys,
            'org_numbers': org_numbers,
            'city_id': city_id,
            'category': category,
            'sort': sort,
            'search_keywords': search_keywords,
        })


class AddUserAskView(View):
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            userask_form.save(commit=True)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'fail', 'msg': '{0}'.format(userask_form.errors)})


class OrgHomeView(View):
    # 机构首页
    def get(self, request, org_id):
        if CourseOrg.objects.filter(pk=org_id).exists():
            course_org = CourseOrg.objects.get(pk=org_id)
        else:
            return render(request, 'org-list.html')
        all_courses = course_org.course_set.all()[:3]
        all_teachers = course_org.teacher_set.all()[:2]
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-homepage.html', {
            'all_courses': all_courses,
            'all_teachers': all_teachers,
            'course_org': course_org,
            'current_page': 'org',
            'has_fav': has_fav,
        })


class OrgCourseView(View):
    # 机构课程列表页
    def get(self, request, org_id):
        if CourseOrg.objects.filter(pk=org_id).exists():
            course_org = CourseOrg.objects.get(pk=org_id)
        else:
            return render(request, 'org-list.html')
        all_courses = course_org.course_set.all()
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-course.html', {
            'all_courses': all_courses,
            'course_org': course_org,
            'current_page': 'courses',
            'has_fav': has_fav,
        })


class OrgDescView(View):
    # 机构描述页
    def get(self, request, org_id):
        if CourseOrg.objects.filter(pk=org_id).exists():
            course_org = CourseOrg.objects.get(pk=org_id)
        else:
            return render(request, 'org-list.html')
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-desc.html', {
            'course_org': course_org,
            'current_page': 'desc',
            'has_fav': has_fav,
        })


class OrgTeacherView(View):
    # 机构讲师页
    def get(self, request, org_id):
        if CourseOrg.objects.filter(pk=org_id).exists():
            course_org = CourseOrg.objects.get(pk=org_id)
        else:
            return render(request, 'org-list.html')
        all_teachers = course_org.teacher_set.all()
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-teachers.html', {
            'course_org': course_org,
            'current_page': 'teacher',
            'all_teachers': all_teachers,
            'has_fav': has_fav,
        })


class AddFavView(View):
    # 用户收藏与取消收藏
    def post(self, request):
        try:
            fav_id = int(request.POST.get('fav_id', 0))
        except ValueError:
            fav_id = 0
        try:
            fav_type = int(request.POST.get('fav_type', 0))
        except ValueError:
            fav_type = 0
        #  过滤掉未取到fav_id type的默认情况
        if fav_id == 0 or fav_type == 0:
            return JsonResponse({'status': 'fail', 'msg': '收藏出错'})
        # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'fail', 'msg': '用户未登录'})
        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=fav_id, fav_type=fav_type)
        # 如果记录已经存在， 则表示用户要取消收藏
        if exist_records:
            exist_records.delete()
            return JsonResponse({'status': 'success', 'msg': '收藏'})
        else:
            user_fav = UserFavorite()
            user_fav.user = request.user
            user_fav.fav_id = fav_id
            user_fav.fav_type = fav_type
            user_fav.save()
            return JsonResponse({'status': 'success', 'msg': '已收藏'})


class TeacherListView(View):
    def get(self, request):
        all_teachers = Teacher.objects.all()
        teacher_nums = all_teachers.count()
        rank_teachers = Teacher.objects.all().order_by('-fav_nums')[:5]
        # 搜索功能
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_teachers = all_teachers.filter(
                Q(name__icontains=search_keywords) |
                Q(work_company__icontains=search_keywords)
            )
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'hot':
                all_teachers.order_by('-click_nums')
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_teachers, 1, request=request)
        teachers = p.page(page)
        return render(request, 'teachers-list.html', {
            'all_teachers': teachers,
            'teacher_nums': teacher_nums,
            'sort': sort,
            'rank_teachers': rank_teachers,
            'search_keywords': search_keywords,
        })


class TeacherDetailView(View):
    def get(self, request, teacher_id):
        teacher = Teacher.objects.get(pk=teacher_id)
        all_courses = teacher.course_set.all()
        rank_teachers = Teacher.objects.all().order_by('-fav_nums')[:5]
        has_fav_teacher = False
        has_fav_org = False
        if UserFavorite.objects.filter(user=request.user, fav_id=teacher.id, fav_type=3):
            has_fav_teacher = True
        if UserFavorite.objects.filter(user=request.user, fav_type=2, fav_id=teacher.org.id):
            has_fav_org = True
        return render(request, 'teacher-detail.html', {
            'teacher': teacher,
            'all_courses': all_courses,
            'rank_teachers': rank_teachers,
            'has_fav_teacher': has_fav_teacher,
            'has_fav_org': has_fav_org,
        })
