from rest_framework import status, pagination, viewsets, permissions, response

from cl.api.utils import LoggingMixin, RECAPUsersReadOnly
from cl.search import api_utils
from cl.search.api_serializers import (
    DocketSerializer, CourtSerializer, OpinionClusterSerializer,
    OpinionSerializer, SearchResultSerializer,
    OpinionsCitedSerializer, DocketEntrySerializer, RECAPDocumentSerializer,
    TagSerializer,
)
from cl.search.filters import (
    DocketFilter, CourtFilter, OpinionClusterFilter, OpinionFilter,
    OpinionsCitedFilter, DocketEntryFilter, RECAPDocumentFilter)
from cl.search.forms import SearchForm
from cl.search.models import Docket, Court, OpinionCluster, Opinion, \
    OpinionsCited, DocketEntry, RECAPDocument, Tag


class DocketViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Docket.objects.all()
    serializer_class = DocketSerializer
    filter_class = DocketFilter
    ordering_fields = (
        'date_created', 'date_modified', 'date_argued', 'date_reargued',
        'date_reargument_denied', 'date_blocked', 'date_cert_granted',
        'date_cert_denied', 'date_filed', 'date_terminated', 'date_last_filing',
    )


class DocketEntryViewSet(LoggingMixin, viewsets.ModelViewSet):
    permission_classes = (RECAPUsersReadOnly,)
    queryset = DocketEntry.objects.all().order_by()
    serializer_class = DocketEntrySerializer
    filter_class = DocketEntryFilter
    ordering_fields = ('date_created', 'date_modified', 'date_filed')


class RECAPDocumentViewSet(LoggingMixin, viewsets.ModelViewSet):
    permission_classes = (RECAPUsersReadOnly,)
    queryset = RECAPDocument.objects.all()
    serializer_class = RECAPDocumentSerializer
    filter_class = RECAPDocumentFilter
    ordering_fields = ('date_created', 'date_modified', 'date_upload')


class CourtViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Court.objects.exclude(jurisdiction='T')
    serializer_class = CourtSerializer
    filter_class = CourtFilter
    ordering_fields = (
        'date_modified', 'position', 'start_date', 'end_date',
    )


class OpinionClusterViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = OpinionCluster.objects.all()
    serializer_class = OpinionClusterSerializer
    filter_class = OpinionClusterFilter
    ordering_fields = (
        'date_created', 'date_modified', 'date_filed', 'citation_count',
        'date_blocked',
    )


class OpinionViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Opinion.objects.all()
    serializer_class = OpinionSerializer
    filter_class = OpinionFilter
    ordering_fields = (
        'id', 'date_created', 'date_modified',
    )


class OpinionsCitedViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = OpinionsCited.objects.all()
    serializer_class = OpinionsCitedSerializer
    filter_class = OpinionsCitedFilter


class TagViewSet(LoggingMixin, viewsets.ModelViewSet):
    permission_classes = (RECAPUsersReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SearchViewSet(LoggingMixin, viewsets.ViewSet):
    # Default permissions use Django permissions, so here we AllowAny, but folks
    # will need to log in to get past the thresholds.
    permission_classes = (permissions.AllowAny,)

    def list(self, request, *args, **kwargs):
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            cd = search_form.cleaned_data
            if cd['q'] == '':
                cd['q'] = '*'  # Get everything

            paginator = pagination.PageNumberPagination()
            sl = api_utils.get_object_list(request, cd=cd, paginator=paginator)

            result_page = paginator.paginate_queryset(sl, request)
            serializer = SearchResultSerializer(
                result_page,
                many=True,
                context={'schema': sl.conn.schema}
            )
            return paginator.get_paginated_response(serializer.data)

        # Invalid search.
        return response.Response(
            search_form.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
