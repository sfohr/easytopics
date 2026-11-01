type DataPoint = {
  x: number;
  y: number;
};

type Series = {
  name: string;
  data: DataPoint[];
};

function generateScatterplotData() {
  // only for development
  const series = [];

  for (let i = 0; i < 100; i++) {
    const dataPoints = [];
    for (let j = 0; j < 10; j++) {
      // Generate random values between -1 and 1 for x and y
      const x = Math.random() * 2 - 1; // Random value between -1 and 1
      const y = Math.random() * 2 - 1; // Random value between -1 and 1

      dataPoints.push({
        x: x,
        y: y,
      });
    }
    series.push({
      name: `Series ${i + 1}`,
      data: dataPoints,
    });
  }

  return series;
}

// transform data from { x: [1, 2, 3], y: [4, 5, 6] } to [{ x: 1, y: 4 }, { x: 2, y: 5 }, { x: 3, y: 6 }] and make Series object
function transformData( // only for development
  name: string,
  inputData: { x: number[]; y: number[] }
): Series[] {
  const { x, y } = inputData;
  const dataPoints: DataPoint[] = [];
  const series = [];

  for (let i = 0; i < x.length; i++) {
    dataPoints.push({ x: x[i], y: y[i] });
  }

  series.push({
    name: name,
    data: dataPoints,
  });

  return series;
}

export default transformData;
