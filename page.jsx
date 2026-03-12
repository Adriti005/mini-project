'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Send, Bot, Wheat, Soup, Flame, Salad, Drumstick, TrendingDown, TrendingUp, Minus } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_WASTE_API_URL ?? 'http://localhost:5000'

export default function PredictPage() {
  const [formData, setFormData] = useState({
    date: '',
    dayOfWeek: 'Monday',
    mealType: 'lunch',
    studentsEnrolled: '',
    averageAttendance: '',
    specialEvent: 'no',
    weather: 'clear',
    holidayPeriod: 'no',
    menusServed: '',
    leftoverFromPreviousDay: '',
  })

  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setPrediction(null)

    try {
      const isNonVeg = ['lunch', 'dinner'].includes(formData.mealType)

      const payload = {
        students_enrolled:        parseInt(formData.studentsEnrolled),
        attendance_percent:       parseFloat(formData.averageAttendance),
        special_event:            formData.specialEvent,
        menu_count:               parseInt(formData.menusServed),
        previous_day_leftover_kg: parseFloat(formData.leftoverFromPreviousDay) || 0,
        nonveg_items:             isNonVeg ? 1 : 0,
        meal_type:                ['dinner','snacks'].includes(formData.mealType) ? 'Dinner' : 'Lunch',
        day:                      formData.dayOfWeek,
      }

      // Use /predict/recommend to get both prediction + recommendations
      const response = await fetch(`${API_URL}/predict/recommend`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body?.error ?? `API error ${response.status}`)
      }

      const data           = await response.json()
      const totalWaste     = data.predicted_waste_kg
      const cost           = Math.round(totalWaste * 25)
      const recommendation = totalWaste > 50 ? 'High' : totalWaste > 30 ? 'Medium' : 'Low'

      setPrediction({
        predictedWaste:  totalWaste,
        cost,
        recommendation,
        confidence:      '91.5',
        insight:         data.insight,
        recommendations: data.recommendations,
      })
    } catch (err) {
      setError(err.message ?? 'Could not reach the prediction API. Is the server running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-emerald-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/" className="p-2 hover:bg-white rounded-lg transition-colors">
            <ArrowLeft className="w-6 h-6 text-gray-600" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Food Wastage Predictor</h1>
            <p className="text-gray-600">Enter hostel details for accurate waste predictions</p>
          </div>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Row 1 */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Date</label>
                <input type="date" name="date" value={formData.date}
                  onChange={handleChange} required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Day of Week</label>
                <select name="dayOfWeek" value={formData.dayOfWeek} onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                  {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Row 2 */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Meal Type</label>
                <select name="mealType" value={formData.mealType} onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                  <option value="breakfast">Breakfast</option>
                  <option value="lunch">Lunch</option>
                  <option value="dinner">Dinner</option>
                  <option value="snacks">Snacks</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Students Enrolled</label>
                <input type="number" name="studentsEnrolled" value={formData.studentsEnrolled}
                  onChange={handleChange} required placeholder="e.g., 500"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                />
              </div>
            </div>

            {/* Row 3 */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Average Attendance (%)</label>
                <input type="number" name="averageAttendance" value={formData.averageAttendance}
                  onChange={handleChange} required min="0" max="100" placeholder="e.g., 85"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Special Event</label>
                <select name="specialEvent" value={formData.specialEvent} onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </div>
            </div>

            {/* Row 4 */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Weather</label>
                <select name="weather" value={formData.weather} onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                  <option value="clear">Clear</option>
                  <option value="cloudy">Cloudy</option>
                  <option value="rainy">Rainy</option>
                  <option value="hot">Hot</option>
                  <option value="cold">Cold</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Holiday Period</label>
                <select name="holidayPeriod" value={formData.holidayPeriod} onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </div>
            </div>

            {/* Row 5 */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Number of Menus Served</label>
                <input type="number" name="menusServed" value={formData.menusServed}
                  onChange={handleChange} required placeholder="e.g., 3"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Leftover from Previous Day (kg)</label>
                <input type="number" name="leftoverFromPreviousDay" value={formData.leftoverFromPreviousDay}
                  onChange={handleChange} placeholder="e.g., 5"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                ⚠️ {error}
              </div>
            )}

            {/* Submit */}
            <button type="submit" disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white font-bold py-4 rounded-lg transition-colors flex items-center justify-center gap-2 text-lg">
              {loading ? (
                <><span className="inline-block animate-spin"><Minus className="w-5 h-5" /></span> Analyzing...</>
              ) : (
                <><Send className="w-5 h-5" /> Get Prediction</>
              )}
            </button>
          </form>
        </div>

        {/* ── Prediction Result ── */}
        {prediction && (
          <div className="space-y-6">

            {/* Result Card */}
            <div className="bg-white rounded-2xl shadow-lg p-8 border-2 border-emerald-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Prediction Results</h2>

              <div className="grid md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-br from-emerald-50 to-transparent p-6 rounded-xl border border-emerald-200">
                  <p className="text-gray-600 text-sm font-medium mb-2">Predicted Waste</p>
                  <p className="text-3xl font-bold text-emerald-600">{prediction.predictedWaste} kg</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-transparent p-6 rounded-xl border border-blue-200">
                  <p className="text-gray-600 text-sm font-medium mb-2">Cost Impact</p>
                  <p className="text-3xl font-bold text-blue-600">₹{prediction.cost}</p>
                </div>
                <div className="bg-gradient-to-br from-amber-50 to-transparent p-6 rounded-xl border border-amber-200">
                  <p className="text-gray-600 text-sm font-medium mb-2">Risk Level</p>
                  <p className={`text-3xl font-bold ${
                    prediction.recommendation === 'High'   ? 'text-red-600' :
                    prediction.recommendation === 'Medium' ? 'text-amber-600' :
                    'text-green-600'
                  }`}>
                    {prediction.recommendation}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-transparent p-6 rounded-xl border border-purple-200">
                  <p className="text-gray-600 text-sm font-medium mb-2">Model R²</p>
                  <p className="text-3xl font-bold text-purple-600">{prediction.confidence}%</p>
                </div>
              </div>

              <div className={`border-l-4 p-4 rounded ${
                prediction.recommendation === 'High'   ? 'bg-red-50 border-red-500' :
                prediction.recommendation === 'Medium' ? 'bg-amber-50 border-amber-500' :
                'bg-blue-50 border-blue-500'
              }`}>
                <p className={
                  prediction.recommendation === 'High'   ? 'text-red-900' :
                  prediction.recommendation === 'Medium' ? 'text-amber-900' :
                  'text-blue-900'
                }>
                  <strong className="flex items-center gap-2"><TrendingUp className="w-4 h-4 inline" /> {prediction.insight.tip}</strong>
                </p>
              </div>
            </div>

            {/* ── AI Recommendations Card ── */}
            {prediction.recommendations && (
              <div className="bg-white rounded-2xl shadow-lg p-8 border-2 border-teal-200">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-teal-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">AI Recommended Cooking Quantities</h2>
                    <p className="text-sm text-gray-500">
                      Optimized by reducing portions by {prediction.recommendations.reduction_percent}% based on waste level
                    </p>
                  </div>
                </div>

                {/* Quantity Grid */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                  {[
                    { label: 'Rice',    value: `${prediction.recommendations.quantities.rice_kg} kg`,   Icon: Wheat },
                    { label: 'Dal',     value: `${prediction.recommendations.quantities.dal_kg} kg`,    Icon: Soup },
                    { label: 'Roti',    value: `${prediction.recommendations.quantities.roti_count}`,   Icon: Flame },
                    { label: 'Veg',     value: `${prediction.recommendations.quantities.veg_kg} kg`,    Icon: Salad },
                    { label: 'Non-Veg', value: `${prediction.recommendations.quantities.nonveg_kg} kg`, Icon: Drumstick },
                  ].map(({ label, value, Icon }) => (
                    <div key={label} className="bg-teal-50 border border-teal-200 rounded-xl p-4 text-center">
                      <div className="flex justify-center mb-2">
                        <Icon className="w-6 h-6 text-teal-500" />
                      </div>
                      <p className="text-xs text-gray-500 font-medium mb-1">{label}</p>
                      <p className="text-lg font-bold text-teal-700">{value}</p>
                    </div>
                  ))}
                </div>

                {/* Waste Comparison */}
                <div className="bg-gray-50 rounded-xl p-5 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Current Predicted Waste</span>
                    <span className="font-bold text-red-600">{prediction.recommendations.current_waste_kg} kg</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Optimized Predicted Waste</span>
                    <span className="font-bold text-emerald-600">{prediction.recommendations.optimized_waste_kg} kg</span>
                  </div>
                  <div className="border-t pt-3 flex justify-between items-center">
                    <span className="text-gray-700 font-semibold">Waste Reduction</span>
                    <span className="font-bold text-teal-600 text-lg flex items-center gap-1">
                        <TrendingDown className="w-5 h-5" />
                        {prediction.recommendations.waste_reduction_kg} kg saved
                      </span>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button onClick={() => setPrediction(null)}
                className="flex-1 px-6 py-3 border-2 border-emerald-600 text-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors font-semibold">
                Make Another Prediction
              </button>
              <Link href="/dashboard"
                className="flex-1 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-semibold text-center">
                View Dashboard
              </Link>
            </div>

          </div>
        )}
      </div>
    </main>
  )
}
