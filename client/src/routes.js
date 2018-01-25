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
    icon: 'pficon pficon-network',
    title: 'Sources',
    to: '/sources',
    redirect: true,
    component: Sources
  },
  {
    icon: 'fa fa-wifi',
    title: 'Scans',
    to: '/scans',
    component: Scans
  },
  {
    icon: 'fa fa-key',
    title: 'Credentials',
    to: '/credentials',
    component: Credentials
  }
];

export { baseName, routes };
