// main.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include "stdafx.h"
#include <stdio.h>
#include <proj.h>

#include "geotiffio.h"
#include "xtiffio.h"
#include <stdlib.h>
#include <string.h>

void SetUpTIFFDirectory(TIFF* tif);
void SetUpGeoKeys(GTIF* gtif);
void WriteImage(TIFF* tif);

#define WIDTH 20L
#define HEIGHT 20L

int main()
{
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
	printf("easting: %zu, northing: %zu\n", static_cast<size_t>(b.enu.e), static_cast<size_t>(b.enu.n));
	b = proj_trans(P, PJ_INV, b);
	printf("longitude: %g, latitude: %g\n", proj_todeg(b.lp.lam), proj_todeg(b.lp.phi));

	/* Clean up */
	proj_destroy(P);
	proj_context_destroy(C); /* may be omitted in the single threaded case */

	auto fname = "newgeo.tif";
	TIFF* tif = nullptr;  /* TIFF-level descriptor */
	GTIF* gtif = nullptr; /* GeoKey-level descriptor */

	tif = XTIFFOpen(fname, "w");
	if (!tif) goto failure;

	gtif = GTIFNew(tif);
	if (!gtif)
	{
		printf("failed in GTIFNew\n");
		goto failure;
	}

	SetUpTIFFDirectory(tif);
	SetUpGeoKeys(gtif);
	WriteImage(tif);

	GTIFWriteKeys(gtif);
	GTIFFree(gtif);
	XTIFFClose(tif);
	return 0;

failure:
	printf("failure in makegeo\n");
	if (tif) TIFFClose(tif);
	if (gtif) GTIFFree(gtif);
	return -1;
}


void SetUpTIFFDirectory(TIFF* tif)
{
	double tiepoints[6] = { 0,0,0,130.0,32.0,0.0 };
	double pixscale[3] = { 1,1,0 };

	TIFFSetField(tif, TIFFTAG_IMAGEWIDTH, WIDTH);
	TIFFSetField(tif, TIFFTAG_IMAGELENGTH, HEIGHT);
	TIFFSetField(tif, TIFFTAG_COMPRESSION, COMPRESSION_NONE);
	TIFFSetField(tif, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK);
	TIFFSetField(tif, TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG);
	TIFFSetField(tif, TIFFTAG_BITSPERSAMPLE, 8);
	TIFFSetField(tif, TIFFTAG_ROWSPERSTRIP, 20L);

	TIFFSetField(tif, TIFFTAG_GEOTIEPOINTS, 6, tiepoints);
	TIFFSetField(tif, TIFFTAG_GEOPIXELSCALE, 3, pixscale);
}

void SetUpGeoKeys(GTIF* gtif)
{
	GTIFKeySet(gtif, GTModelTypeGeoKey, TYPE_SHORT, 1, ModelGeographic);
	GTIFKeySet(gtif, GTRasterTypeGeoKey, TYPE_SHORT, 1, RasterPixelIsArea);
	GTIFKeySet(gtif, GTCitationGeoKey, TYPE_ASCII, 0, "Just An Example");
	GTIFKeySet(gtif, GeographicTypeGeoKey, TYPE_SHORT, 1, KvUserDefined);
	GTIFKeySet(gtif, GeogCitationGeoKey, TYPE_ASCII, 0, "Everest Ellipsoid Used.");
	GTIFKeySet(gtif, GeogAngularUnitsGeoKey, TYPE_SHORT, 1, Angular_Degree);
	GTIFKeySet(gtif, GeogLinearUnitsGeoKey, TYPE_SHORT, 1, Linear_Meter);
	GTIFKeySet(gtif, GeogGeodeticDatumGeoKey, TYPE_SHORT, 1, KvUserDefined);
	GTIFKeySet(gtif, GeogEllipsoidGeoKey, TYPE_SHORT, 1, Ellipse_Everest_1830_1967_Definition);
	GTIFKeySet(gtif, GeogSemiMajorAxisGeoKey, TYPE_DOUBLE, 1, (double)6377298.556);
	GTIFKeySet(gtif, GeogInvFlatteningGeoKey, TYPE_DOUBLE, 1, (double)300.8017);
}

void WriteImage(TIFF* tif)
{
	int i;
	char buffer[WIDTH];

	memset(buffer, 0, (size_t)WIDTH);
	for (i = 0; i < HEIGHT; i++)
		if (!TIFFWriteScanline(tif, buffer, i, 0))
			TIFFError("WriteImage", "failure in WriteScanline\n");
}
