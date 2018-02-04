import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Grid,
  EmptyState,
  Row,
  ListView,
  Modal
} from 'patternfly-react';

import { bindMethods } from '../../common/helpers';
import Store from '../../redux/store';
import { toastNotificationTypes } from '../../redux/constants';
import { getScans } from '../../redux/actions/scansActions';

import ScansToolbar from './scansToolbar';
import SourcesEmptyState from '../sources/sourcesEmptyState';
import { ScanListItem } from './scanListItem';

class Scans extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'downloadSummaryReport',
      'downloadDetailedReport',
      'pauseScan',
      'cancelScan',
      'startScan',
      'addSource',
      'importSources',
      'refresh'
    ]);
    this.state = {
      filteredItems: []
    };
  }

  componentDidMount() {
    this.props.getScans();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.scans !== this.props.scans) {
      nextProps.scans.forEach(scan => {
        scan.systems_scanned = Math.abs(scan.systems_scanned) % 100;
        scan.systems_failed = Math.abs(scan.systems_failed) % 100;
        scan.scans_count = Math.floor(Math.random() * 10);

        // TODO: Get real hosts or wait until expansion?
        scan.hosts = [];
        for (let i = 0; i < scan.systems_scanned; i++) {
          scan.hosts.push('host' + (i + 1));
        }
        scan.failed_hosts = [];
        for (let i = 0; i < scan.systems_failed; i++) {
          scan.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      let filteredItems = this.filterScans(
        nextProps.scans,
        nextProps.activeFilters
      );

      this.setState({ filteredItems: filteredItems, selectedItems: [] });
    } else if (nextProps.activeFilters !== this.props.activeFilters) {
      let filteredItems = this.filterScans(
        nextProps.scans,
        nextProps.activeFilters
      );
      this.setState({ filteredItems: filteredItems });
    }
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return (item.id + '').match(re) !== null; // Using ID for now until we get a name
      case 'status':
        return item.status === filter.value.id;
      case 'scanType':
        return item.scan_type === filter.value.id;
      default:
        return true;
    }
  }

  matchesFilters(item, filters) {
    let matches = true;

    filters.forEach(filter => {
      if (!this.matchesFilter(item, filter)) {
        matches = false;
        return false;
      }
    });
    return matches;
  }

  filterScans(scans, filters) {
    return scans.filter(item => {
      return this.matchesFilters(item, filters);
    });
  }

  sortScans(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.id - item2.id; // Using ID for now until we get a name
          break;
        case 'status':
          compValue = item1.status.localeCompare(item2.status);
          if (compValue === 0) {
            compValue = item1.scan_type.localeCompare(item2.scan_type);
          }
          break;
        case 'scanType':
          compValue = item1.scan_type.localeCompare(item2.scan_type);
          if (compValue === 0) {
            compValue = item1.status.localeCompare(item2.status);
          }
          break;
        case 'sourceCount':
          compValue = item1.sources.length - item2.sources.length;
          if (compValue === 0) {
            compValue = item1.status.localeCompare(item2.status);
            if (compValue === 0) {
              compValue = item1.scan_type.localeCompare(item2.scan_type);
            }
          }
          break;
        default:
          compValue = 0;
      }

      if (!sortAscending) {
        compValue = compValue * -1;
      }

      return compValue;
    });
  }

  downloadSummaryReport() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading summary reports is not yet implemented'
    });
  }

  downloadDetailedReport() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading summary reports is not yet implemented'
    });
  }

  pauseScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Pausing scans is not yet implemented'
    });
  }

  cancelScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Cancelling scans is not yet implemented'
    });
  }

  startScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Starting scans is not yet implemented'
    });
  }

  addSource() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Adding sources is not yet implemented'
    });
  }

  importSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Importing sources is not yet implemented'
    });
  }

  refresh() {
    this.props.getScans();
  }

  renderList(items) {
    return (
      <Row>
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <ScanListItem
              item={item}
              key={index}
              onSummaryDownload={this.downloadSummaryReport}
              onDetailedDownload={this.downloadDetailedReport}
              onPause={this.pauseScan}
              onCancel={this.cancelScan}
              onStart={this.startScan}
            />
          ))}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, scans } = this.props;
    const { filteredItems } = this.state;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading scans...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving scans: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }
    if (scans && scans.length) {
      this.sortScans(filteredItems);

      return (
        <div className="quipucords-view-container">
          <ScansToolbar
            totalCount={scans.length}
            filteredCount={filteredItems.length}
            onRefresh={this.refresh}
          />
          <Grid fluid className="quipucords-list-container">
            {this.renderList(filteredItems)}
          </Grid>
        </div>
      );
    }
    return (
      <SourcesEmptyState
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />
    );
  }
}

Scans.propTypes = {
  getScans: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  scans: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Scans.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScans: () => dispatch(getScans())
});

function mapStateToProps(state) {
  return {
    loading: state.scans.loading,
    scans: state.scans.data,
    loadError: state.scans.error,
    errorMessage: state.scans.errorMessage,
    activeFilters: state.scansToolbar.activeFilters,
    sortType: state.scansToolbar.sortType,
    sortAscending: state.scansToolbar.sortAscending
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Scans);
