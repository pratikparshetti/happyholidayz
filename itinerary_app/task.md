# Fix UI Population for Flights, Hotels, and Trains

## Root Cause
The `numHotels`, `numFlights`, and `numTrains` input fields lack the `name` attribute, so FormData doesn't capture them when saving. When loading, the app can't generate the correct number of forms, leaving no fields to populate.

## Tasks

- [x] **Add `name` attributes to count inputs**
  - [x] Add `name="numHotels"` to the hotels count input (line 270)
  - [x] Add `name="numFlights"` to the flights count input (line 281)
  - [x] Add `name="numTrains"` to the trains count input (line 292)

- [x] **Fix duplicate function call bug**
  - [x] Remove the erroneous `generateHotelForms(parseInt(formData.numFlights))` call on line 786
  - [x] Keep only `generateFlightForms(parseInt(formData.numFlights))` for the flights section

- [ ] **Test the fix**
  - [ ] Create a new project with 1 hotel, 1 flight, 1 train
  - [ ] Save the project
  - [ ] Reload the page
  - [ ] Load the saved project
  - [ ] Verify all forms are generated and populated correctly

## Note
This fix will only work for **newly saved** projects. Old JSON files saved before this fix won't have the count data and will need manual editing or a migration script to work properly.
