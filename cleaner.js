async function fetchLecturerInfo(lecturerId) {
  const baseUrl = "https://cloud.timeedit.net/my_um/web/students/";
  const url = `${baseUrl}objects/${lecturerId}/o.json?fr=t&types=15&sid=5&l=en_US`;

  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

async function processLecturerBatch(batchIds) {
  const promises = batchIds.map(async lecturerId => {
    const data = await fetchLecturerInfo(lecturerId);
    return data?.hasOwnProperty("Job Category") ? { id: lecturerId, details: data } : null;
  });

  const results = await Promise.all(promises);
  return results.filter(Boolean);
}

async function processLecturersConcurrently() {
  const startLecturerId = 8600;
  const endLecturerId = 13700;
  const batchSize = 100; // Increased batch size
  const concurrencyLimit = 10; // Matches browser's max parallel requests
  let allLecturerData = [];
  const allBatches = [];

  console.log(`Fetching lecturer data for IDs ${startLecturerId} to ${endLecturerId}`);

  // Generate all batches first
  for (let i = startLecturerId; i <= endLecturerId; i += batchSize) {
    allBatches.push(
      Array.from({ length: Math.min(batchSize, endLecturerId - i + 1) })
        .map((_, j) => i + j)
    );
  }

  // Process batches in concurrent groups
  for (let i = 0; i < allBatches.length; i += concurrencyLimit) {
    const batchGroup = allBatches.slice(i, i + concurrencyLimit);
    console.log(`Processing group ${i + 1}-${i + batchGroup.length} of ${allBatches.length}`);
    
    const groupResults = await Promise.all(
      batchGroup.map(batch => processLecturerBatch(batch))
    );
    
    allLecturerData.push(...groupResults.flat());
  }

  console.log("Fetching complete. Total lecturers:", allLecturerData.length);

  if (allLecturerData.length > 0) {
    // Create and trigger download
    const blob = new Blob([JSON.stringify(allLecturerData, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'lecturer_data.json';
    a.click();
    console.log("JSON file downloaded");
  }
}

processLecturersConcurrently();
