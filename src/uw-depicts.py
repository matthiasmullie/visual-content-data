#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Run on a stat host; or just paste into pyspark3 console over there

from pyspark.sql import functions as F
from wmfdata.spark import create_session

spark = create_session(
    app_name='visual-content-data-uw-depicts',
)

uw_upload_revisions = spark.sql('SELECT * FROM wmf_content.mediawiki_content_history_v1')
uw_upload_revisions = uw_upload_revisions.where(uw_upload_revisions.wiki_id == 'commonswiki')
uw_upload_revisions = uw_upload_revisions.where(uw_upload_revisions.page_namespace_id == 6)
uw_upload_revisions = uw_upload_revisions.where(uw_upload_revisions.revision_parent_id.isNull())
uw_upload_revisions = uw_upload_revisions.where(uw_upload_revisions.revision_comment.contains('UploadWizard'))
uw_upload_revisions = uw_upload_revisions.where(uw_upload_revisions.revision_dt > F.lit('2019-01-01 00:00:00'))

mediainfo_revisions = spark.sql('SELECT * FROM wmf_content.mediawiki_content_history_v1')
mediainfo_revisions = mediainfo_revisions.where(mediainfo_revisions.wiki_id == 'commonswiki')
mediainfo_revisions = mediainfo_revisions.where(mediainfo_revisions.page_namespace_id == 6)
mediainfo_revisions = mediainfo_revisions.where(mediainfo_revisions.revision_content_slots.mediainfo.content_body.isNotNull())

join = (mediainfo_revisions
    .join(
        uw_upload_revisions,
        on=[
            mediainfo_revisions.page_id == uw_upload_revisions.page_id,
            mediainfo_revisions.revision_dt < uw_upload_revisions.revision_dt + F.expr('INTERVAL 1 MINUTE'),
            ],
        how='inner',
    )
)

uploads = (uw_upload_revisions
    .groupBy(F.to_date(uw_upload_revisions.revision_dt, 'yyyy-MM-dd').alias('date'))
    .count()
    .sort(F.asc('date'))
)

uploads_with_captions = (join
    .where(mediainfo_revisions.revision_content_slots.mediainfo.content_body.contains('"language":'))
    .select(uw_upload_revisions.page_id, uw_upload_revisions.revision_dt)
    .distinct()
    .groupBy(F.to_date(uw_upload_revisions.revision_dt, 'yyyy-MM-dd').alias('date'))
    .count()
    .sort(F.asc('date'))
)

captions = (join
    .where(mediainfo_revisions.revision_content_slots.mediainfo.content_body.contains('"language":'))
    .withColumn('amount_of_captions', F.size(F.split(mediainfo_revisions.revision_content_slots.mediainfo.content_body, '"language":')) -1)
    .groupBy(F.to_date(uw_upload_revisions.revision_dt, 'yyyy-MM-dd').alias('date'))
    .agg(F.sum('amount_of_captions').alias('captions_count'))
    .sort(F.asc('date'))
)

uploads_with_depicts = (join
    .where(mediainfo_revisions.revision_content_slots.mediainfo.content_body.contains('"P180":'))
    .select(uw_upload_revisions.page_id, uw_upload_revisions.revision_dt)
    .distinct()
    .groupBy(F.to_date(uw_upload_revisions.revision_dt, 'yyyy-MM-dd').alias('date'))
    .count()
    .sort(F.asc('date'))
)

depicts_statements = (join
    .where(mediainfo_revisions.revision_content_slots.mediainfo.content_body.contains('"P180":'))
    .withColumn('amount_of_depicts', F.size(F.split(mediainfo_revisions.revision_content_slots.mediainfo.content_body, '"P180":')) -1)
    .groupBy(F.to_date(uw_upload_revisions.revision_dt, 'yyyy-MM-dd').alias('date'))
    .agg(F.sum('amount_of_depicts').alias('depicts_count'))
    .sort(F.asc('date'))
)

print('All UW uploads')
uploads.show(uploads.count())

print('UW uploads with captions')
uploads_with_captions.show(uploads_with_captions.count())

print('Amount of captions')
captions.show(captions.count())

print('UW uploads with depicts')
uploads_with_depicts.show(uploads_with_depicts.count())

print('Amount of depicts')
depicts_statements.show(depicts_statements.count())
