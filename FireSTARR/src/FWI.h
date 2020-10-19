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

#pragma once
#include <string>
#include "Weather.h"
namespace firestarr
{
namespace wx
{
/**
 * \brief Fine Fuel Moisture Code value.
 */
class Ffmc : public Index<Ffmc>
{
public:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
  /**
   * \brief Calculate Fine Fuel Moisture Code
   * \param temperature Temperature (Celcius)
   * \param rh Relative Humidity (%)
   * \param wind Wind (km/h)
   * \param rain Accumulated Precipitation (mm)
   * \param ffmc_previous Fine Fuel Moisture Code for previous day
   */
  Ffmc(const Temperature& temperature,
       const RelativeHumidity& rh,
       const Speed& wind,
       const AccumulatedPrecipitation& rain,
       const Ffmc& ffmc_previous) noexcept;
  /**
   * \brief Fine Fuel Moisture Code of 0
   */
  static const Ffmc Zero;
};
/**
 * \brief Duff Moisture Code value.
 */
class Dmc : public Index<Dmc>
{
public:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
  /**
   * \brief Duff Moisture Code
   * \param temperature Temperature (Celcius)
   * \param rh Relative Humidity (%)
   * \param rain Accumulated Precipitation (mm)
   * \param dmc_previous Duff Moisture Code for previous day
   * \param month Month to calculate for
   * \param latitude Latitude to calculate for
   */
  Dmc(const Temperature& temperature,
      const RelativeHumidity& rh,
      const AccumulatedPrecipitation& rain,
      const Dmc& dmc_previous,
      int month,
      double latitude) noexcept;
  /**
   * \brief Duff Moisture Code of 0
   */
  static const Dmc Zero;
};
/**
 * \brief Drought Code value.
 */
class Dc : public Index<Dc>
{
public:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
  /**
   * \brief Calculate Drought Code
   * \param temperature Temperature (Celcius)
   * \param rain Accumulated Precipitation (mm)
   * \param dc_previous Drought Code from the previous day
   * \param month Month to calculate for
   * \param latitude Latitude to calculate for
   */
  Dc(const Temperature& temperature,
     const AccumulatedPrecipitation& rain,
     const Dc& dc_previous,
     int month,
     double latitude) noexcept;
  /**
   * \brief Drought Code of 0
   */
  static const Dc Zero;
};
/**
 * \brief Initial Spread Index value.
 */
class Isi : public Index<Isi>
{
public:
  /**
   * \brief Calculate Initial Spread Index and verify previous value is within tolerance of calculated value
   * \param value Value to check is within tolerance of calculated value
   * \param wind Wind Speed (km/h)
   * \param ffmc Fine Fuel Moisture Code
   */
  Isi(double value, const Speed& wind, const Ffmc& ffmc) noexcept;
  /**
   * \brief Calculate Initial Spread Index
   * \param wind Wind Speed (km/h)
   * \param ffmc Fine Fuel Moisture Code
   */
  Isi(const Speed& wind, const Ffmc& ffmc) noexcept;
  /**
   * \brief Initial Spread Index of 0
   */
  static const Isi Zero;
private:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
};
/**
 * \brief Build-up Index value.
 */
class Bui : public Index<Bui>
{
public:
  /**
   * \brief Calculate Build-up Index and verify previous value is within tolerance of calculated value
   * \param value Value to check is within tolerance of calculated value
   * \param dmc Duff Moisture Code
   * \param dc Drought Code
   */
  Bui(double value, const Dmc& dmc, const Dc& dc) noexcept;
  /**
   * \brief Calculate Build-up Index
   * \param dmc Duff Moisture Code
   * \param dc Drought Code
   */
  Bui(const Dmc& dmc, const Dc& dc) noexcept;
  /**
   * \brief Build-up Index of 0
   */
  static const Bui Zero;
private:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
};
/**
 * \brief Fire Weather Index value.
 */
class Fwi : public Index<Fwi>
{
public:
  /**
   * \brief Calculate Fire Weather Index and verify previous value is within tolerance of calculated value
   * \param value Value to check is within tolerance of calculated value
   * \param isi Initial Spread Index
   * \param bui Build-up Index
   */
  Fwi(double value, const Isi& isi, const Bui& bui) noexcept;
  /**
   * \brief Calculate Fire Weather Index
   * \param isi Initial Spread Index
   * \param bui Build-up Index
   */
  Fwi(const Isi& isi, const Bui& bui) noexcept;
  /**
   * \brief Fire Weather Index of 0
   */
  static const Fwi Zero;
private:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
};
/**
 * \brief Danger Severity Rating value.
 */
class Dsr : public Index<Dsr>
{
public:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
  /**
   * \brief Calculate Danger Severity Rating
   * \param fwi Fire Weather Index
   */
  explicit Dsr(const Fwi& fwi) noexcept;
  /**
   * \brief Danger Severity Rating of 0
   */
  static const Dsr Zero;
};
/**
 * \brief A Weather value with calculated FWI indices.
 */
class FwiWeather
  : public Weather
{
public:
  /**
   * \brief FwiWeather with 0 for all Indices
   */
  static const FwiWeather Zero;
  /**
   * \brief Construct with 0 for all values
   */
  FwiWeather() noexcept;
  /**
   * \brief Construct by reading from a Database
   * \param db Database to read from
   */
  explicit FwiWeather(util::Database* db) noexcept;
  /**
   * \brief Construct by reading from istringstream
   * \param iss Stream to parse
   * \param str string to read into
   */
  FwiWeather(istringstream* iss, string* str);
  /**
   * \brief Constructor
   * \param tmp Temperature (Celcius)
   * \param rh Relative Humidity (%)
   * \param wind Wind (km/h)
   * \param apcp Accumulated Precipitation (mm)
   * \param ffmc Fine Fuel Moisture Code
   * \param dmc Duff Moisture Code
   * \param dc Drought Code
   * \param isi Initial Spread Index
   * \param bui Build-up Index
   * \param fwi Fire Weather Index
   */
  FwiWeather(const Temperature& tmp,
             const RelativeHumidity& rh,
             const Wind& wind,
             const AccumulatedPrecipitation& apcp,
             const Ffmc& ffmc,
             const Dmc& dmc,
             const Dc& dc,
             const Isi& isi,
             const Bui& bui,
             const Fwi& fwi) noexcept;
  /**
   * \brief Construct by recalculating with different wind Speed and Ffmc
   * \param wx Original weather values
   * \param ws Wind Speed to use
   * \param ffmc Fine Fuel Moisture Code to use
   */
  FwiWeather(const FwiWeather& wx, const Speed& ws, const Ffmc& ffmc) noexcept;
  /**
   * \brief Destructor
   */
  ~FwiWeather() = default;
  /**
   * \brief Move constructor
   * \param rhs FwiWeather to move from
   */
  constexpr FwiWeather(FwiWeather&& rhs) noexcept = default;
  /**
   * \brief Copy constructor
   * \param rhs FwiWeather to copy from
   */
  constexpr FwiWeather(const FwiWeather& rhs) noexcept = default;
#pragma warning (push)
#pragma warning (disable: 26456)
  /**
   * \brief Move assignment
   * \param rhs FwiWeather to move from
   * \return This, after assignment
   */
  FwiWeather& operator=(FwiWeather&& rhs) noexcept = default;
  /**
   * \brief Copy assignment
   * \param rhs FwiWeather to copy from
   * \return This, after assignment
   */
  FwiWeather& operator=(const FwiWeather& rhs) = default;
#pragma warning (pop)
  /**
   * \brief Fine Fuel Moisture Code
   * \return Fine Fuel Moisture Code
   */
  [[nodiscard]] constexpr const Ffmc& ffmc() const { return ffmc_; }
  /**
   * \brief Duff Moisture Code
   * \return Duff Moisture Code
   */
  [[nodiscard]] constexpr const Dmc& dmc() const { return dmc_; }
  /**
   * \brief Drought Code
   * \return Drought Code
   */
  [[nodiscard]] constexpr const Dc& dc() const { return dc_; }
  /**
   * \brief Initial Spread Index
   * \return Initial Spread Index
   */
  [[nodiscard]] constexpr const Isi& isi() const { return isi_; }
  /**
   * \brief Build-up Index
   * \return Build-up Index
   */
  [[nodiscard]] constexpr const Bui& bui() const { return bui_; }
  /**
   * \brief Fire Weather Index
   * \return Fire Weather Index
   */
  [[nodiscard]] constexpr const Fwi& fwi() const { return fwi_; }
  /**
   * \brief Moisture content (%) based on Ffmc
   * \return Moisture content (%) based on Ffmc
   */
  [[nodiscard]] constexpr double mcFfmcPct() const { return mc_ffmc_pct_; }
  /**
   * \brief Moisture content (%) based on Dmc
   * \return Moisture content (%) based on Dmc
   */
  [[nodiscard]] constexpr double mcDmcPct() const { return mc_dmc_pct_; }
  /**
   * \brief Moisture content (ratio) based on Ffmc
   * \return Moisture content (ratio) based on Ffmc
   */
  [[nodiscard]] constexpr double mcFfmc() const { return mcFfmcPct() / 100.0; }
  /**
   * \brief Moisture content (ratio) based on Dmc
   * \return Moisture content (ratio) based on Dmc
   */
  [[nodiscard]] constexpr double mcDmc() const { return mcDmcPct() / 100.0; }
  /**
   * \brief Ffmc effect used for spread
   * \return Ffmc effect used for spread
   */
  [[nodiscard]] constexpr double ffmcEffect() const { return ffmc_effect_; }
private:
  /**
   * \brief Calculate based on indices plus new Wind, Ffmc, and Isi
   * \param wx FwiWeather to use most indices from
   * \param wind Wind to override with
   * \param ffmc Ffmc to override with
   * \param isi Isi calculated from given Wind and Ffmc to override with
   */
  FwiWeather(const FwiWeather& wx,
             const Wind& wind,
             const Ffmc& ffmc,
             const Isi& isi) noexcept;
  /**
   * \brief Calculate based on indices plus new Wind and Ffmc
   * \param wx FwiWeather to use most indices from
   * \param wind Wind to override with
   * \param ffmc Ffmc to override with
   */
  FwiWeather(const FwiWeather& wx, const Wind& wind, const Ffmc& ffmc) noexcept;
  /**
   * \brief Fine Fuel Moisture Code
   */
  Ffmc ffmc_;
  /**
   * \brief Duff Moisture Code
   */
  Dmc dmc_;
  /**
   * \brief Drought Code
   */
  Dc dc_;
  /**
   * \brief Initial Spread Index
   */
  Isi isi_;
  /**
   * \brief Build-up Index
   */
  Bui bui_;
  /**
   * \brief Fire Weather Index
   */
  Fwi fwi_;
  /**
   * \brief Moisture content (ratio) based on Ffmc
   */
  double mc_ffmc_pct_;
  /**
   * \brief Moisture content (ratio) based on Dmc
   */
  double mc_dmc_pct_;
  /**
   * \brief Ffmc effect used for spread
   */
  double ffmc_effect_;
};
[[nodiscard]] constexpr bool operator<(const FwiWeather& lhs, const FwiWeather& rhs)
{
  if (lhs.tmp() == rhs.tmp())
  {
    if (lhs.rh() == rhs.rh())
    {
      if (lhs.wind() == rhs.wind())
      {
        if (lhs.apcp() == rhs.apcp())
        {
          if (lhs.ffmc() == rhs.ffmc())
          {
            if (lhs.dmc() == rhs.dmc())
            {
              if (lhs.dc() == rhs.dc())
              {
                assert(lhs.isi() == rhs.isi());
                assert(lhs.bui() == rhs.bui());
                assert(lhs.fwi() == rhs.fwi());
              }
              return lhs.dc() < rhs.dc();
            }
            return lhs.dmc() < rhs.dmc();
          }
          return lhs.ffmc() < rhs.ffmc();
        }
        return lhs.apcp() < rhs.apcp();
      }
      return lhs.wind() < rhs.wind();
    }
    return lhs.rh() < rhs.rh();
  }
  return lhs.tmp() < rhs.tmp();
}
[[nodiscard]] constexpr bool operator!=(const FwiWeather& lhs, const FwiWeather& rhs)
{
  return lhs.tmp() != rhs.tmp()
    || lhs.rh() != rhs.rh()
    || lhs.wind() != rhs.wind()
    || lhs.apcp() != rhs.apcp()
    || lhs.ffmc() != rhs.ffmc()
    || lhs.dmc() != rhs.dmc()
    || lhs.dc() != rhs.dc()
    || lhs.isi() != rhs.isi()
    || lhs.bui() != rhs.bui()
    || lhs.fwi() != rhs.fwi();
}
[[nodiscard]] constexpr bool operator==(const FwiWeather& lhs, const FwiWeather& rhs)
{
  return !(lhs != rhs);
}
}
}
