/**
 * Return array of objects that describe vertical menu
 * @return {array}
 */
const getMenu = () => [
  {
    icon: 'pficon pficon-network',
    title: 'Sources',
    to: '/sources'
  },
  {
    icon: 'fa fa-list-alt',
    title: 'Scans',
    to: '/scans'
  }
];

export { getMenu };
