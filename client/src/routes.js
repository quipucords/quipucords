import Scans from './components/scans/scans';
import Sources from './components/sources/sources';

const baseName = '/client';

/**
 * Return array of objects that describe vertical menu
 * @return {array}
 */
const routes = () => [
  {
    icon: 'pficon pficon-network',
    title: 'Sources',
    to: '/sources',
    redirect: true,
    component: Sources
  },
  {
    icon: 'fa fa-list-alt',
    title: 'Scans',
    to: '/scans',
    component: Scans
  }
];

export { baseName, routes };
