import Scans from './components/scans/scans';
import Sources from './components/sources/sources';
import Credentials from './components/credentials/credentials';

const baseName = '/client';

/**
 * Return array of objects that describe vertical menu
 * @return {array}
 */
const routes = () => [
  {
    iconClass: 'fa fa-crosshairs',
    title: 'Sources',
    to: '/sources',
    redirect: true,
    component: Sources
  },
  {
    iconClass: 'pficon pficon-orders',
    title: 'Scans',
    to: '/scans',
    component: Scans
  },
  {
    iconClass: 'fa fa-id-card',
    title: 'Credentials',
    to: '/credentials',
    component: Credentials
  }
];

export { baseName, routes };
