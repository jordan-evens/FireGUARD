// main.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include "stdafx.h"
#include <stdio.h>
#include <proj.h>

int main(void) {
    PJ_CONTEXT* C;
    PJ* P;
    PJ_COORD a, b;

    /* or you may set C=PJ_DEFAULT_CTX if you are sure you will     */
    /* use PJ objects from only one thread                          */
    C = proj_context_create();

    P = proj_create(C, "+proj=utm +zone=15 +ellps=GRS80");
    if (0 == P)
        return puts("Oops"), 0;

    /* a coordinate union representing Copenhagen: 55d N, 12d E    */
    /* note: PROJ.4 works in radians, hence the proj_torad() calls */
    a = proj_coord(proj_torad(-93.8634523), proj_torad(51.0348531), 0, 0);

    /* transform to UTM zone 15, then back to geographical */
    b = proj_trans(P, PJ_FWD, a);
    printf("easting: %g, northing: %g\n", b.enu.e, b.enu.n);
    b = proj_trans(P, PJ_INV, b);
    printf("longitude: %g, latitude: %g\n", proj_todeg(b.lp.lam), proj_todeg(b.lp.phi));

    /* Clean up */
    proj_destroy(P);
    proj_context_destroy(C); /* may be omitted in the single threaded case */
    return 0;
}
