#include <visual.hpp>

#ifdef __cplusplus
extern "C" {
#endif

KMETHOD MouseEvent_lastScreenPos(CTX ctx, knh_sfp_t *sfp _RIX)
{
	QGraphicsSceneMouseEvent *event = RawPtr_to(QGraphicsSceneMouseEvent *, sfp[0]);
	QPointF spos = event->lastScreenPos();
	KPoint *p = new KPoint(spos.x(), spos.y());
	RETURN_(new_RawPtr(ctx, sfp[1].p, p));
}

static void MouseEvent_free(CTX ctx, knh_RawPtr_t *p)
{
	(void)ctx;
	fprintf(stderr, "MouseEvent:free\n");
	QGraphicsSceneMouseEvent *event = (QGraphicsSceneMouseEvent *)p->rawptr;
	delete event;
}

static void MouseEvent_reftrace(CTX ctx, knh_RawPtr_t *p FTRARG)
{
	(void)ctx;
	(void)p;
	(void)tail_;
	fprintf(stderr, "MouseEvent:reftrace\n");
	//QApplication *app = (QApplication *)p->rawptr;
}

DEFAPI(void) defMouseEvent(CTX ctx, knh_class_t cid, knh_ClassDef_t *cdef)
{
	NO_WARNING2();
	cdef->name = "MouseEvent";
	cdef->free = MouseEvent_free;
	cdef->reftrace = MouseEvent_reftrace;
}

DEFAPI(void) constMouseEvent(CTX ctx, knh_class_t cid, const knh_PackageLoaderAPI_t *kapi)
{
	(void)ctx;
	(void)cid;
	(void)kapi;
	//kapi->loadIntClassConst(ctx, cid, TimeLineConstInt);
}

#ifdef __cplusplus
}
#endif
