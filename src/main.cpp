// Copyright (C) 2020  Jordan Evens
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// 
// Last Updated 2020-05-13 by Jordan Evens

#include <proj.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "geotiffio.h"
#include "stdafx.h"
#include "xtiffio.h"
enum { VERSION = 0, MAJOR, MINOR };
void SetUpTIFFDirectory(TIFF* tif);
void SetUpGeoKeys(GTIF* gtif);
void WriteImage(TIFF* tif);
#define WIDTH 20L
#define HEIGHT 20L
int main()
{
  TIFFSetWarningHandler(nullptr);
  PJ_CONTEXT* C;
  PJ* P;
  PJ_COORD a, b;
  /* or you may set C=PJ_DEFAULT_CTX if you are sure you will     */
  /* use PJ objects from only one thread                          */
  C = proj_context_create();
  P = proj_create(C, "+proj=utm +zone=15 +ellps=GRS80");
  if (nullptr == P)
    return puts("Oops"), 0;
  /* a coordinate union representing Copenhagen: 55d N, 12d E    */
  /* note: PROJ.4 works in radians, hence the proj_torad() calls */
  a = proj_coord(proj_torad(-93.8634523), proj_torad(51.0348531), 0, 0);
  /* transform to UTM zone 15, then back to geographical */
  b = proj_trans(P, PJ_FWD, a);
  printf("easting: %zu, northing: %zu\n",
         static_cast<size_t>(b.enu.e),
         static_cast<size_t>(b.enu.n));
  b = proj_trans(P, PJ_INV, b);
  printf("longitude: %g, latitude: %g\n", proj_todeg(b.lp.lam), proj_todeg(b.lp.phi));
  /* Clean up */
  proj_destroy(P);
  proj_context_destroy(C); /* may be omitted in the single threaded case */
  auto fname = "newgeo.tif";
  auto from_file = "gis/grid/aspect_14_5.tif";
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
  // reading test
  tif = (TIFF*)nullptr;  /* TIFF-level descriptor */
  gtif = (GTIF*)nullptr; /* GeoKey-level descriptor */
  int versions[3];
  int length;
  geocode_t model;    /* all key-codes are of this type */
  char* citation;
  char* nodata;
  /* Open TIFF descriptor to read GeoTIFF tags */
  tif = XTIFFOpen(from_file, "r");
  if (!tif) goto failure;
  /* Open GTIF Key parser; keys will be read at this time. */
  gtif = GTIFNew(tif);
  if (!gtif) goto failure;
  /* Get the GeoTIFF directory info */
  GTIFDirectoryInfo(gtif, versions, nullptr);
  if (versions[MAJOR] > 1)
  {
    printf("this file is too new for me\n");
    goto failure;
  }
  if (!GTIFKeyGet(gtif, GTModelTypeGeoKey, &model, 0, 1))
  {
    printf("Yikes! no Model Type\n");
    goto failure;
  }
  int size;
  uint32* width;
  tagtype_t type;
  /* ASCII keys are variable-length; compute size */
  length = GTIFKeyInfo(gtif, GTCitationGeoKey, &size, &type);
  if (length > 0)
  {
    citation = (char*)malloc(size * length);
    if (!citation) goto failure;
    GTIFKeyGet(gtif, GTCitationGeoKey, citation, 0, length);
    printf("Citation:%s\n", citation);
  }
  if (TIFFGetField(tif, TIFFTAG_GDAL_NODATA, &length, &nodata) && length > 0)
  {
    printf("NoData:%s\n", nodata);
  }
  /* Get some TIFF info on this image */
  TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &width);
  if (tif)
  {
    uint32 imageWidth, imageLength;
    uint32 tileWidth, tileLength;
    uint32 x, y;
    tdata_t buf;
    auto scanline_size = TIFFScanlineSize(tif);
    auto strip_size = TIFFStripSize(tif);
    TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &imageWidth);
    TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &imageLength);
    TIFFGetField(tif, TIFFTAG_TILEWIDTH, &tileWidth);
    TIFFGetField(tif, TIFFTAG_TILELENGTH, &tileLength);
    printf("%zux%zu", tileWidth, tileLength);
    buf = _TIFFmalloc(TIFFTileSize(tif));
    for (y = 0; y < imageLength; y += tileLength)
      for (x = 0; x < imageWidth; x += tileWidth)
        TIFFReadTile(tif, buf, x, y, 0, 0);
    _TIFFfree(buf);
  }
  /* get rid of the key parser */
  GTIFFree(gtif);
  /* close the TIFF file descriptor */
  XTIFFClose(tif);
  exit(0);
failure:
  printf("failure in makegeo\n");
  if (tif) TIFFClose(tif);
  if (gtif) GTIFFree(gtif);
  return -1;
}
void SetUpTIFFDirectory(TIFF* tif)
{
  double tiepoints[6] = {0, 0, 0, 130.0, 32.0, 0.0};
  double pixscale[3] = {1, 1, 0};
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
  GTIFKeySet(gtif,
             GeogEllipsoidGeoKey,
             TYPE_SHORT,
             1,
             Ellipse_Everest_1830_1967_Definition);
  GTIFKeySet(gtif, GeogSemiMajorAxisGeoKey, TYPE_DOUBLE, 1, (double)6377298.556);
  GTIFKeySet(gtif, GeogInvFlatteningGeoKey, TYPE_DOUBLE, 1, (double)300.8017);
}
void WriteImage(TIFF* tif)
{
  char buffer[WIDTH];
  memset(buffer, 0, (size_t)WIDTH);
  for (int i = 0; i < HEIGHT; i++)
    if (!TIFFWriteScanline(tif, buffer, i, 0))
      TIFFError("WriteImage", "failure in WriteScanline\n");
}
