import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Button,
  EmptyState,
  Icon,
  ListView,
  Modal
} from 'patternfly-react';

import { getSources } from '../../redux/actions/sourcesActions';
import {
  sourcesTypes,
  toastNotificationTypes,
  confirmationModalTypes,
  viewTypes
} from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';

import SourcesEmptyState from './sourcesEmptyState';
import { SourceListItem } from './sourceListItem';
import { CreateScanDialog } from './createScanDialog';
import AddSourceWizard from '../addSourceWizard/addSourceWizard';
import { SourceFilterFields, SourceSortFields } from './sourceConstants';

class Sources extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'importSources',
      'scanSource',
      'scanSources',
      'itemSelectChange',
      'editSource',
      'deleteSource',
      'hideScanDialog',
      'createScan',
      'refresh',
      'showAddSourceWizard'
    ]);

    this.state = {
      scanDialogShown: false,
      multiSourceScan: false,
      currentScanSource: null,
      addSourceWizardShown: false
    };
  }

  componentDidMount() {
    this.props.getSources(
      helpers.createViewQueryObject(this.props.viewOptions)
    );
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.sources && nextProps.sources !== this.props.sources) {
      // TODO: Remove once we get real failed host data
      nextProps.sources.forEach(source => {
        let failedCount = Math.floor(Math.random() * 10);
        source.failed_hosts = [];
        for (let i = 0; i < failedCount; i++) {
          source.failed_hosts.push('failedHost' + (i + 1));
        }
      });
    }

    // Check for changes resulting in a fetch
    if (
      helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)
    ) {
      this.props.getSources(
        helpers.createViewQueryObject(nextProps.viewOptions)
      );
    }
  }

  itemSelected(item) {
    const { selectedSources } = this.props;
    return (
      selectedSources.find(nextSelected => {
        return nextSelected.id === _.get(item, 'id');
      }) !== undefined
    );
  }

  showAddSourceWizard() {
    Store.dispatch({
      type: sourcesTypes.EDIT_SOURCE_SHOW
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

  scanSource(source) {
    this.setState({
      scanDialogShown: true,
      multiSourceScan: false,
      currentScanSource: source
    });
  }

  scanSources() {
    this.setState({ scanDialogShown: true, multiSourceScan: true });
  }

  hideScanDialog() {
    this.setState({ scanDialogShown: false });
  }

  itemSelectChange(item) {
    Store.dispatch({
      type: this.itemSelected(item)
        ? sourcesTypes.DESELECT_SOURCE
        : sourcesTypes.SELECT_SOURCE,
      source: item
    });
  }

  editSource(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Editing sources is not yet implemented'
    });
  }

  doDeleteSource(item) {
    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Deleting sources is not yet implemented'
    });
  }

  deleteSource(item) {
    let heading = (
      <span>
        Are you sure you want to delete the source <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteSource(item);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  createScan(scanName, sources) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: scanName,
      message: 'Scanning sources is not yet implemented'
    });
    this.hideScanDialog();
  }

  refresh() {
    this.props.getSources();
  }

  renderSourceActions() {
    const { selectedSources } = this.props;

    return (
      <div className="form-group">
        <Button bsStyle="primary" onClick={this.showAddSourceWizard}>
          Add
        </Button>
        <Button
          disabled={!selectedSources || selectedSources.length === 0}
          onClick={this.scanSources}
        >
          Scan
        </Button>
        <Button onClick={this.refresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
        </Button>
      </div>
    );
  }

  renderSourcesList(items) {
    return (
      <ListView className="quipicords-list-view">
        {items.map((item, index) => (
          <SourceListItem
            item={item}
            selected={this.itemSelected(item)}
            key={index}
            onItemSelectChange={this.itemSelectChange}
            onEdit={this.editSource}
            onDelete={this.deleteSource}
            onScan={this.scanSource}
          />
        ))}
      </ListView>
    );
  }

  render() {
    const {
      pending,
      error,
      errorMessage,
      sources,
      selectedSources,
      viewOptions
    } = this.props;
    const {
      scanDialogShown,
      multiSourceScan,
      currentScanSource,
      addSourceWizardShown
    } = this.state;

    if (pending) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (sources && sources.length) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.SOURCES_VIEW}
              filterFields={SourceFilterFields}
              sortFields={SourceSortFields}
              actions={this.renderSourceActions()}
              itemsType="Source"
              itemsTypePlural="Sources"
              selectedCount={selectedSources.length}
              {...viewOptions}
            />
            <div className="quipucords-list-container">
              {this.renderSourcesList(sources)}
            </div>
            <ViewPaginationRow
              viewType={viewTypes.SOURCES_VIEW}
              {...viewOptions}
            />
          </div>
          <AddSourceWizard show={addSourceWizardShown} />
          <CreateScanDialog
            show={scanDialogShown}
            sources={multiSourceScan ? selectedSources : [currentScanSource]}
            onCancel={this.hideScanDialog}
            onScan={this.createScan}
          />
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState
          onAddSource={this.showAddSourceWizard}
          onImportSources={this.importSources}
        />
        <AddSourceWizard show={addSourceWizardShown} />
      </React.Fragment>
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  sources: PropTypes.array,
  selectedSources: PropTypes.array,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: queryObj => dispatch(getSources(queryObj))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.sources.view, state.sources.persist, {
    viewOptions: state.viewOptions[viewTypes.SOURCES_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(Sources);
