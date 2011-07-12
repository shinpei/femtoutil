#include <visual.hpp>

#ifdef __cplusplus
extern "C" {
#endif

KMETHOD Item_translate(CTX ctx, knh_sfp_t *sfp _RIX)
{
	NO_WARNING();
	QGraphicsItem *i = KITEM_to(sfp[0].p);
	int x = Int_to(int, sfp[1]);
	int y = Int_to(int, sfp[2]);
	i->translate(x, y);
	RETURNvoid_();
}

KMETHOD Item_setTransform(CTX ctx, knh_sfp_t *sfp _RIX)
{
	NO_WARNING();
	QGraphicsItem *i = KITEM_to(sfp[0].p);
	QTransform *t = RawPtr_to(QTransform *, sfp[1]);
	int b = Boolean_to(int, sfp[2]);
	i->setTransform(*t, b);
	RETURNvoid_();
}

#ifdef __cplusplus
}
#endif
