// Copyright (C) 2020  Queen's Printer for Ontario
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
// Last Updated 2020-04-07 <Evens, Jordan (MNRF)>

#include "stdafx.h"
#include "Startup.h"
#include "TimeUtil.h"
namespace firestarr
{
namespace wx
{
Startup::Startup(string station,
                 const TIMESTAMP_STRUCT& generated,
                 const topo::Point& point,
                 const double distance_from,
                 const Ffmc& ffmc,
                 const Dmc& dmc,
                 const Dc& dc,
                 const AccumulatedPrecipitation& apcp_0800,
                 const bool overridden) noexcept
  : station_(std::move(station)),
    generated_(generated),
    point_(point),
    distance_from_(distance_from),
    ffmc_(ffmc),
    dmc_(dmc),
    dc_(dc),
    apcp_0800_(apcp_0800),
    is_overridden_(overridden)
{
}
}
}
